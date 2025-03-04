from typing import List, Dict, Optional
import openai
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
import os
from datetime import datetime

class NLUEngine:
    def __init__(self):
        # Initialize GPT-4
        self.openai = openai
        self.openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize Llama 2
        self.tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf")
        self.llama_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-chat-hf")
        
        # Context management
        self.conversation_history = []
        self.max_history = 10
        
        # Load task definitions and examples
        self.task_definitions = self._load_task_definitions()

    def _load_task_definitions(self) -> Dict:
        """Load predefined task patterns and responses"""
        return {
            "calendar": {
                "patterns": ["schedule", "appointment", "meeting", "remind", "calendar"],
                "required_params": ["date", "time", "description"]
            },
            "email": {
                "patterns": ["send email", "write email", "compose", "mail to"],
                "required_params": ["recipient", "subject", "content"]
            },
            "weather": {
                "patterns": ["weather", "temperature", "forecast"],
                "required_params": ["location", "time"]
            },
            "smart_home": {
                "patterns": ["turn on", "turn off", "adjust", "set temperature"],
                "required_params": ["device", "action"]
            }
        }

    def _extract_intent(self, query: str) -> Dict:
        """Use GPT-4 to extract intent and entities from the query"""
        prompt = f"""
        Analyze the following query and extract the intent and entities:
        Query: {query}
        
        Provide output in JSON format with:
        - Main intent
        - Sub-intent (if any)
        - Entities (key-value pairs)
        - Required follow-up questions (if missing critical information)
        """
        
        response = self.openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an intent classification system. Extract structured information from queries."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return json.loads(response.choices[0].message.content)

    def _generate_llama_response(self, query: str, context: Dict) -> str:
        """Use Llama 2 for generating detailed, context-aware responses"""
        # Format conversation history and context
        context_prompt = f"""
        Previous context: {json.dumps(context)}
        User query: {query}
        Based on the above context and query, provide a helpful response.
        """
        
        inputs = self.tokenizer(context_prompt, return_tensors="pt")
        outputs = self.llama_model.generate(
            inputs["input_ids"],
            max_length=200,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def process_query(self, query: str, user_context: Optional[Dict] = None) -> Dict:
        """
        Process a natural language query with context awareness
        """
        try:
            # Extract intent and entities using GPT-4
            intent_analysis = self._extract_intent(query)
            
            # Update conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "intent": intent_analysis
            })
            
            # Trim history if needed
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            # Combine current context with user context and history
            current_context = {
                "conversation_history": self.conversation_history,
                "user_context": user_context or {},
                "current_intent": intent_analysis
            }
            
            # Generate response using Llama 2
            response = self._generate_llama_response(query, current_context)
            
            # Check if follow-up questions are needed
            follow_up_questions = intent_analysis.get("required_follow_up", [])
            
            return {
                "response": response,
                "intent": intent_analysis,
                "follow_up_questions": follow_up_questions,
                "requires_more_info": len(follow_up_questions) > 0
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "response": "I apologize, but I encountered an error processing your request."
            }

    def update_context(self, user_id: str, context_update: Dict):
        """Update user-specific context"""
        if not hasattr(self, 'user_contexts'):
            self.user_contexts = {}
        
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {}
            
        self.user_contexts[user_id].update(context_update)

    def get_context(self, user_id: str) -> Dict:
        """Retrieve user-specific context"""
        return self.user_contexts.get(user_id, {})
