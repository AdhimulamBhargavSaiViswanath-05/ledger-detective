"""
Intelligent Pipeline - Enhanced pipeline with AI capabilities
"""
from typing import Dict, Any, Optional
from src.chains.sql_generation import generate_sql, get_llm_state
from src.chains.validation import validate_sql
from src.chains.execution import execute_sql
from src.chains.answer_composition import compose_answer
from src.intelligence import (
    ConversationContext,
    AnomalyDetector,
    SmartSuggester,
    QueryDecomposer
)


class IntelligentPipeline:
    """Enhanced pipeline with conversation context, anomaly detection, and smart suggestions"""
    
    def __init__(self):
        self.context = ConversationContext()
        self.anomaly_detector = AnomalyDetector()
        self.suggester = SmartSuggester()
        self.decomposer = QueryDecomposer()
    
    def run_query(self, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run intelligent query with all enhancements
        
        Returns:
            - question: Original question
            - sql_query: Generated SQL
            - raw_result: Raw DB result
            - answer: Natural language answer
            - steps: Processing steps
            - suggestions: Follow-up question suggestions
            - anomalies: Detected issues (if any)
            - context_used: Whether conversation context was used
            - decomposition_plan: If complex query was decomposed
        """
        result_data = {
            "question": question,
            "sql_query": "",
            "raw_result": "",
            "answer": "",
            "steps": [],
            "suggestions": [],
            "anomalies": None,
            "context_used": False,
            "decomposition_plan": None,
            "error": None,
            "llm_mode": None,
            "llm_fallback_reason": None
        }
        
        # Check for special commands
        if question.lower().strip() in ['scan for issues', 'check for anomalies', 'run health check']:
            return self._run_anomaly_scan()
        
        # Step 0: Check if query needs decomposition
        if self.decomposer.should_decompose(question):
            steps = self.decomposer.decompose(question)
            decomp_plan = self.decomposer.format_execution_plan(steps)
            if decomp_plan:
                result_data["decomposition_plan"] = decomp_plan
                result_data["steps"].append(f"🧩 Complex query detected - decomposing into {len(steps)} steps")
        
        # Step 1: Resolve references using conversation context
        original_question = question
        if len(self.context.history) > 0:
            question = self.context.resolve_references(question)
            if question != original_question:
                result_data["context_used"] = True
                result_data["steps"].append(f"🔗 Using conversation context to resolve references")
                result_data["steps"].append(f"   Resolved: '{original_question}' → '{question}'")
        
        result_data["steps"].append("📝 Analyzing question and determining intent")
        
        # Step 2: Generate SQL
        try:
            context_info = self.context.get_context_for_query()
            sql = generate_sql(question)
            
            # Check LLM state
            llm_state = get_llm_state()
            result_data["llm_mode"] = llm_state.get("mode")
            result_data["llm_fallback_reason"] = llm_state.get("fallback_reason")
            
            if llm_state.get("mode") == "gemini":
                result_data["steps"].append("✅ Generated SQL using Gemini AI")
            else:
                result_data["steps"].append("✅ Generated SQL using Mock LLM")
                if llm_state.get("fallback_reason"):
                    result_data["steps"].append(f"⚠️  Fallback reason: {llm_state['fallback_reason']}")
        except Exception as e:
            result_data["error"] = f"Error generating SQL: {str(e)}"
            result_data["answer"] = result_data["error"]
            return result_data
        
        # Check LLM decisions
        if sql.startswith("OUT_OF_SCOPE:"):
            reason = sql.replace("OUT_OF_SCOPE:", "").strip()
            result_data["steps"].append("🚫 Question determined to be out of scope")
            result_data["answer"] = reason
            result_data["suggestions"] = self.suggester.suggest_proactive_actions()
            return result_data
        
        if sql.startswith("NEEDS_CLARIFICATION:"):
            clarification = sql.replace("NEEDS_CLARIFICATION:", "").strip()
            result_data["steps"].append("❓ Question is ambiguous, requesting clarification")
            result_data["answer"] = clarification
            return result_data
        
        result_data["sql_query"] = sql
        
        # Step 3: Validate SQL
        result_data["steps"].append("🔒 Validating SQL query for security")
        is_valid, validation_reason = validate_sql(sql)
        if not is_valid:
            result_data["error"] = f"Query failed safety checks: {validation_reason}"
            result_data["answer"] = result_data["error"]
            result_data["steps"].append(f"❌ Validation failed: {validation_reason}")
            return result_data
        result_data["steps"].append("✅ SQL query passed all security validations")
        
        # Step 4: Execute SQL
        result_data["steps"].append("⚡ Executing query against database")
        success, result, _ = execute_sql(sql)
        if not success:
            result_data["error"] = f"Error executing query: {result}"
            result_data["answer"] = result_data["error"]
            result_data["steps"].append(f"❌ Execution failed: {result}")
            return result_data
        
        result_data["raw_result"] = result
        result_data["steps"].append(f"✅ Query executed successfully")
        
        # Step 5: Compose answer
        result_data["steps"].append("💬 Composing natural language answer")
        try:
            answer = compose_answer(question, result)
            result_data["answer"] = answer
            result_data["steps"].append("✅ Answer generated successfully")
        except Exception as e:
            result_data["error"] = f"Error composing answer: {str(e)}"
            result_data["answer"] = result_data["error"]
            result_data["steps"].append(f"❌ Answer composition failed: {str(e)}")
            return result_data
        
        # Step 6: Generate smart suggestions
        result_data["steps"].append("💡 Generating follow-up suggestions")
        result_data["suggestions"] = self.suggester.suggest_followups(
            question, answer, sql, result
        )
        
        # Step 7: Add to conversation context
        self.context.add_turn(question, sql, result, answer)
        
        # Step 8: Check for anomalies (periodically)
        # Run anomaly detection every 5 queries
        if len(self.context.history) % 5 == 0:
            result_data["steps"].append("🔍 Running periodic anomaly scan")
            anomalies = self.anomaly_detector.scan_all()
            if anomalies:
                result_data["anomalies"] = {
                    'count': len(anomalies),
                    'message': self.anomaly_detector.generate_alert_message(anomalies),
                    'details': [a.to_dict() for a in anomalies]
                }
        
        return result_data
    
    def _run_anomaly_scan(self) -> Dict[str, Any]:
        """Run full anomaly detection scan"""
        result_data = {
            "question": "Run anomaly detection scan",
            "sql_query": "",
            "raw_result": "",
            "answer": "",
            "steps": [],
            "suggestions": [],
            "anomalies": None,
            "context_used": False,
            "decomposition_plan": None,
            "error": None
        }
        
        result_data["steps"].append("🔍 Starting comprehensive anomaly detection scan")
        
        anomalies = self.anomaly_detector.scan_all()
        
        if anomalies:
            result_data["answer"] = self.anomaly_detector.generate_alert_message(anomalies)
            result_data["anomalies"] = {
                'count': len(anomalies),
                'message': result_data["answer"],
                'details': [a.to_dict() for a in anomalies]
            }
            result_data["steps"].append(f"⚠️ Found {len(anomalies)} anomalies")
        else:
            result_data["answer"] = "✅ No issues detected. All procurement data looks good!"
            result_data["steps"].append("✅ Scan complete - no anomalies found")
        
        result_data["suggestions"] = [
            "Show me the details of specific issues",
            "Generate a comprehensive data report",
            "What actions should I take?"
        ]
        
        return result_data
    
    def get_proactive_insights(self) -> Dict[str, Any]:
        """Get proactive insights without specific question"""
        # Run anomaly detection
        anomalies = self.anomaly_detector.scan_all()
        
        # Get quick stats
        quick_insights = self.suggester.get_quick_insights(self.anomaly_detector.db)
        
        return {
            'anomalies': [a.to_dict() for a in anomalies] if anomalies else [],
            'quick_insights': quick_insights,
            'suggestions': self.suggester.suggest_proactive_actions()
        }
    
    def clear_context(self):
        """Clear conversation context (new chat)"""
        self.context.clear()
    
    def get_context_summary(self) -> str:
        """Get conversation context summary"""
        return self.context.get_summary()


# Global instance (for stateless usage)
_global_pipeline = None

def get_intelligent_pipeline() -> IntelligentPipeline:
    """Get or create global intelligent pipeline instance"""
    global _global_pipeline
    if _global_pipeline is None:
        _global_pipeline = IntelligentPipeline()
    return _global_pipeline


def run_intelligent_query(question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Run query through intelligent pipeline"""
    pipeline = get_intelligent_pipeline()
    return pipeline.run_query(question, session_id)
