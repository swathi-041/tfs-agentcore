"""
QnA Agent for TFS AgentCore Runtime
Handles Bedrock Knowledge Base retrieval and answering
"""
import os
import json
import boto3
import re
from typing import Dict, Any


class QnAAgent:
    """QnA Agent with Bedrock Knowledge Base integration"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=config["AWS_REGION"]
        )
        self.bedrock_agent_runtime = boto3.client(
            service_name="bedrock-agent-runtime",
            region_name=config["AWS_REGION"]
        )
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """
        Process a question using Bedrock Knowledge Base RAG
        
        Args:
            question: User question
            
        Returns:
            Dict with question and answer
        """
        try:
            user_question = question.strip()

            # 1️⃣ Retrieve from Bedrock Knowledge Base
            retrieval_response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.config["KNOWLEDGE_BASE_ID"],
                retrievalQuery={
                    "text": user_question
                },
                retrievalConfiguration={
                    "vectorSearchConfiguration": {
                        "numberOfResults": 8
                    }
                }
            )

            retrieval_results = retrieval_response.get("retrievalResults", [])

            # 2️⃣ Handle no retrieval
            if not retrieval_results:
                return {
                    "question": user_question,
                    "answer": "I don't have information about this in the TFS knowledge base. This topic may be out of scope or not available."
                }

            # 3️⃣ Filter chunks + source ranking
            filtered_chunks = []
            source_map = []

            for item in retrieval_results:
                text = item.get("content", {}).get("text", "")
                score = item.get("score", 0)

                found_urls = re.findall(r'https?://[^\s]+', text)

                if len(text.strip()) > 80 and score >= 0.70:
                    filtered_chunks.append(text)

                    for url in found_urls:
                        source_map.append((url, score))

            # 4️⃣ fallback if filtering removes all chunks
            if not filtered_chunks:
                for item in retrieval_results[:5]:
                    text = item.get("content", {}).get("text", "")
                    if text:
                        filtered_chunks.append(text)

                        found_urls = re.findall(r'https?://[^\s]+', text)
                        for url in found_urls:
                            source_map.append((url, item.get("score", 0)))

            # 5️⃣ Remove duplicate chunks
            unique_chunks = []
            seen_chunks = set()

            for chunk in filtered_chunks:
                normalized = chunk.strip()

                if normalized not in seen_chunks:
                    unique_chunks.append(chunk)
                    seen_chunks.add(normalized)

            retrieved_context = "\n\n".join(unique_chunks[:5])

            # 6️⃣ Rank source URLs
            sorted_sources = sorted(
                source_map,
                key=lambda x: x[1],
                reverse=True
            )

            unique_urls = []
            seen_urls = set()

            for url, score in sorted_sources:
                clean_url = url.strip().rstrip(".,)")

                if clean_url not in seen_urls:
                    unique_urls.append(clean_url)
                    seen_urls.add(clean_url)

            url_text = "\n".join(unique_urls[:3])

            # 7️⃣ Prompt
            prompt = f"""
You are the official Toyota Financial Services virtual assistant.

────────────────────
ROLE
────────────────────
Answer ONLY using retrieved Toyota Financial Services knowledge base content.

────────────────────
PRIORITY
────────────────────
The main answer must be complete, useful, and sufficiently detailed before generating extra sections.

If multiple valid details exist, include all of them clearly.

Do not shorten the answer just to fit other sections.

────────────────────
RULES
────────────────────
- Use ONLY retrieved context
- Ignore unrelated context
- Answer fully enough to satisfy the user
- Include all relevant points
- Use bullet points where helpful
- Do NOT hallucinate
- Do NOT use external knowledge
- Do NOT omit important details

────────────────────
SPECIAL CASES
────────────────────
If unrelated:
"I am a TFS assistant and can only answer questions related to Toyota Financial Services."

If no answer exists:
"I don't have information about this in the TFS knowledge base. This topic may be out of scope or not available."

If greeting:
"Hi, I'm the Toyota Financial Services virtual assistant."

────────────────────
MANDATORY RESPONSE FORMAT
────────────────────
Answer:
Provide full answer first.
If multiple options exist, explain each clearly.

Related Questions:
Generate 2 to 3 highly relevant follow-up questions.

Next Steps:
Include actionable steps only if applicable.

Sources:
Include ALL relevant public URLs that support the answer.
If multiple URLs are relevant, include all unique URLs.
One URL per line.

────────────────────
RETRIEVED CONTEXT
────────────────────
{retrieved_context}

────────────────────
AVAILABLE URLS
────────────────────
{url_text}

────────────────────
QUESTION
────────────────────
{user_question}
""".strip()

            # 8️⃣ Invoke Bedrock Model
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 1800,
                    "temperature": 0.1,
                    "topP": 0.9
                }
            }

            response = self.bedrock_runtime.invoke_model(
                modelId=self.config["BEDROCK_MODEL_ID"],
                body=json.dumps(payload),
                contentType="application/json",
                accept="application/json"
            )

            response_body = json.loads(response["body"].read())

            answer = (
                response_body
                .get("output", {})
                .get("message", {})
                .get("content", [{}])[0]
                .get("text", "")
                .strip()
            )

            # 9️⃣ Final Response
            return {
                "question": user_question,
                "answer": answer
            }

        except Exception as e:
            return {
                "question": question,
                "answer": f"Error processing question: {str(e)}"
            }
