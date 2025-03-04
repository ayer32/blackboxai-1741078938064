from typing import Dict, List, Any, Optional, Union
import torch
import tensorflow as tf
import numpy as np
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline,
    GPT2LMHeadModel,
    GPT2Tokenizer
)
import openai
from sentence_transformers import SentenceTransformer
import tensorflow_hub as hub
from sklearn.metrics.pairwise import cosine_similarity
import logging
import os
from dotenv import load_dotenv

load_dotenv()

class MLFramework:
    def __init__(self):
        self.setup_logging()
        self.initialize_models()
        self.setup_openai()

    def setup_logging(self):
        """Set up logging for ML operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('ml_framework')

    def initialize_models(self):
        """Initialize various ML models"""
        try:
            # Text Generation Model (GPT-2)
            self.text_generator = pipeline(
                'text-generation',
                model='gpt2',
                device=0 if torch.cuda.is_available() else -1
            )

            # Sentiment Analysis
            self.sentiment_analyzer = pipeline(
                'sentiment-analysis',
                model='distilbert-base-uncased-finetuned-sst-2-english'
            )

            # Text Embeddings
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

            # Question Answering
            self.qa_model = pipeline(
                'question-answering',
                model='deepset/roberta-base-squad2'
            )

            # Text Classification
            self.classifier = pipeline(
                'text-classification',
                model='distilbert-base-uncased'
            )

            # Load Universal Sentence Encoder
            self.use_model = hub.load(
                "https://tfhub.dev/google/universal-sentence-encoder/4"
            )

            self.logger.info("ML models initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing ML models: {str(e)}")
            raise

    def setup_openai(self):
        """Set up OpenAI integration"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        else:
            self.logger.warning("OpenAI API key not found")

    async def generate_text(
        self,
        prompt: str,
        max_length: int = 100,
        use_openai: bool = True
    ) -> str:
        """Generate text using either OpenAI or local model"""
        try:
            if use_openai and self.openai_api_key:
                response = await openai.Completion.acreate(
                    engine="text-davinci-003",
                    prompt=prompt,
                    max_tokens=max_length,
                    temperature=0.7
                )
                return response.choices[0].text.strip()
            else:
                outputs = self.text_generator(
                    prompt,
                    max_length=max_length,
                    num_return_sequences=1
                )
                return outputs[0]['generated_text']

        except Exception as e:
            self.logger.error(f"Text generation error: {str(e)}")
            raise

    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text"""
        try:
            result = self.sentiment_analyzer(text)[0]
            return {
                "label": result["label"],
                "score": float(result["score"])
            }
        except Exception as e:
            self.logger.error(f"Sentiment analysis error: {str(e)}")
            raise

    async def get_embeddings(
        self,
        texts: Union[str, List[str]]
    ) -> np.ndarray:
        """Get text embeddings"""
        try:
            if isinstance(texts, str):
                texts = [texts]
            return self.embedding_model.encode(texts)
        except Exception as e:
            self.logger.error(f"Embedding generation error: {str(e)}")
            raise

    async def answer_question(
        self,
        context: str,
        question: str
    ) -> Dict[str, Any]:
        """Answer questions based on context"""
        try:
            result = self.qa_model(
                question=question,
                context=context
            )
            return {
                "answer": result["answer"],
                "score": float(result["score"]),
                "start": result["start"],
                "end": result["end"]
            }
        except Exception as e:
            self.logger.error(f"Question answering error: {str(e)}")
            raise

    async def classify_text(
        self,
        text: str,
        labels: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Classify text into categories"""
        try:
            result = self.classifier(text, labels)
            return {
                "label": result[0]["label"],
                "score": float(result[0]["score"])
            }
        except Exception as e:
            self.logger.error(f"Text classification error: {str(e)}")
            raise

    async def calculate_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """Calculate semantic similarity between texts"""
        try:
            embeddings = self.use_model([text1, text2])
            similarity = cosine_similarity(
                embeddings.numpy()[0:1],
                embeddings.numpy()[1:2]
            )
            return float(similarity[0][0])
        except Exception as e:
            self.logger.error(f"Similarity calculation error: {str(e)}")
            raise

    async def summarize_text(
        self,
        text: str,
        max_length: int = 130,
        min_length: int = 30
    ) -> str:
        """Generate text summary"""
        try:
            summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn"
            )
            summary = summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            return summary[0]['summary_text']
        except Exception as e:
            self.logger.error(f"Text summarization error: {str(e)}")
            raise

    async def translate_text(
        self,
        text: str,
        target_language: str
    ) -> str:
        """Translate text to target language"""
        try:
            translator = pipeline(
                "translation",
                model=f"Helsinki-NLP/opus-mt-en-{target_language}"
            )
            translation = translator(text)
            return translation[0]['translation_text']
        except Exception as e:
            self.logger.error(f"Translation error: {str(e)}")
            raise

    async def extract_keywords(
        self,
        text: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Extract keywords from text"""
        try:
            extractor = pipeline(
                "token-classification",
                model="dbmdz/bert-large-cased-finetuned-conll03-english"
            )
            results = extractor(text)
            
            # Group and count entities
            keywords = {}
            for result in results:
                word = result['word']
                score = result['score']
                if word in keywords:
                    keywords[word] = max(keywords[word], score)
                else:
                    keywords[word] = score

            # Sort and return top k keywords
            sorted_keywords = sorted(
                keywords.items(),
                key=lambda x: x[1],
                reverse=True
            )
            return [
                {"word": k, "score": float(v)}
                for k, v in sorted_keywords[:top_k]
            ]
        except Exception as e:
            self.logger.error(f"Keyword extraction error: {str(e)}")
            raise

    async def generate_image_caption(
        self,
        image_tensor: torch.Tensor
    ) -> str:
        """Generate caption for image"""
        try:
            captioner = pipeline(
                "image-to-text",
                model="nlpconnect/vit-gpt2-image-captioning"
            )
            caption = captioner(image_tensor)
            return caption[0]['generated_text']
        except Exception as e:
            self.logger.error(f"Image captioning error: {str(e)}")
            raise

    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language of text"""
        try:
            detector = pipeline(
                "text-classification",
                model="papluca/xlm-roberta-base-language-detection"
            )
            result = detector(text)
            return {
                "language": result[0]["label"],
                "confidence": float(result[0]["score"])
            }
        except Exception as e:
            self.logger.error(f"Language detection error: {str(e)}")
            raise
