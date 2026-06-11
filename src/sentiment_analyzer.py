#!/usr/bin/env python3
"""
Azure Cognitive Services Sentiment Analysis Learning Program
Author: AI Coding Assistant (Antigravity)
Date: June 11, 2026

This script performs batch sentiment analysis and opinion mining using the 
Azure Cognitive Services Language SDK. It securely loads credentials from 
environment variables and provides a simulated mock client if credentials are unset.
"""

import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any, Union

# Azure Language Service SDK Imports
try:
    from azure.ai.textanalytics import TextAnalyticsClient
    from azure.core.credentials import AzureKeyCredential
    from azure.core.exceptions import AzureError
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

# ==========================================
# SIMULATED MOCK CLIENT (For local runs / fallback)
# ==========================================

class MockConfidenceScores:
    def __init__(self, positive: float, neutral: float, negative: float):
        self.positive = positive
        self.neutral = neutral
        self.negative = negative

class MockTargetConfidenceScores:
    def __init__(self, positive: float, negative: float):
        self.positive = positive
        self.negative = negative

class MockTarget:
    def __init__(self, text: str, sentiment: str, positive: float, negative: float):
        self.text = text
        self.sentiment = sentiment
        self.confidence_scores = MockTargetConfidenceScores(positive, negative)

class MockAssessment:
    def __init__(self, text: str, sentiment: str, positive: float, negative: float, is_negated: bool = False):
        self.text = text
        self.sentiment = sentiment
        self.confidence_scores = MockTargetConfidenceScores(positive, negative)
        self.is_negated = is_negated

class MockOpinion:
    def __init__(self, target: MockTarget, assessments: List[MockAssessment]):
        self.target = target
        self.assessments = assessments

class MockSentence:
    def __init__(self, text: str, sentiment: str, positive: float, neutral: float, negative: float, opinions: List[MockOpinion] = None):
        self.text = text
        self.sentiment = sentiment
        self.confidence_scores = MockConfidenceScores(positive, neutral, negative)
        self.opinions = opinions or []

class MockAnalyzeSentimentResult:
    def __init__(self, id: str, sentiment: str, positive: float, neutral: float, negative: float, sentences: List[MockSentence], is_error: bool = False, opinions: List[MockOpinion] = None):
        self.id = id
        self.sentiment = sentiment
        self.confidence_scores = MockConfidenceScores(positive, neutral, negative)
        self.sentences = sentences
        self.is_error = is_error
        self.opinions = opinions or []

class MockTextAnalyticsClient:
    """Simulates Azure TextAnalyticsClient using exact data models."""
    def __init__(self):
        # Database of mock responses mapped by doc ID or content snippet
        self.mock_db = {
            "1": MockAnalyzeSentimentResult("1", "positive", 0.9872, 0.0086, 0.0042, [
                MockSentence("I absolutely love this laptop!", "positive", 0.9951, 0.0031, 0.0018),
                MockSentence("The battery life is outstanding and the display is crystal clear.", "positive", 0.9901, 0.0067, 0.0032),
                MockSentence("Best purchase I've made this year.", "positive", 0.9765, 0.0160, 0.0075)
            ]),
            "2": MockAnalyzeSentimentResult("2", "negative", 0.0031, 0.0119, 0.9850, [
                MockSentence("The customer service was terrible.", "negative", 0.0012, 0.0045, 0.9943),
                MockSentence("I waited 3 hours and nobody helped me.", "negative", 0.0021, 0.0088, 0.9891),
                MockSentence("The product quality is also below average.", "negative", 0.0098, 0.0312, 0.9590),
                MockSentence("Very disappointed.", "negative", 0.0015, 0.0045, 0.9940)
            ]),
            "3": MockAnalyzeSentimentResult("3", "neutral", 0.1423, 0.7654, 0.0923, [
                MockSentence("The package arrived on time.", "neutral", 0.2341, 0.7234, 0.0425),
                MockSentence("The product works as described.", "neutral", 0.1876, 0.7643, 0.0481),
                MockSentence("Nothing extraordinary but nothing bad either.", "neutral", 0.0512, 0.8087, 0.1401)
            ]),
            "4": MockAnalyzeSentimentResult("4", "mixed", 0.4823, 0.0712, 0.4465, [
                MockSentence("Great camera and smooth performance,", "positive", 0.9123, 0.0567, 0.0310),
                MockSentence("but the charging speed is frustratingly slow", "negative", 0.0234, 0.0412, 0.9354),
                MockSentence("and the price is way too high for what you get.", "negative", 0.0312, 0.0567, 0.9121)
            ]),
            "5": MockAnalyzeSentimentResult("5", "positive", 0.8145, 0.1023, 0.0832, [
                MockSentence("This coffee maker produces the most amazing espresso I've ever tasted.", "positive", 0.9812, 0.0134, 0.0054),
                MockSentence("The build quality feels premium.", "positive", 0.9345, 0.0521, 0.0134),
                MockSentence("The milk frother could be better though.", "negative", 0.0823, 0.1934, 0.7243)
            ]),
            "om1": MockAnalyzeSentimentResult("om1", "mixed", 0.4912, 0.0234, 0.4854, [
                MockSentence("The food was delicious and the portions were generous,", "positive", 0.9534, 0.0312, 0.0154),
                MockSentence("but the service was painfully slow and the restaurant was noisy.", "negative", 0.0143, 0.0312, 0.9545)
            ], opinions=[
                # Simulated sentence opinion format matching SDK
                # Sentence 1: "The food was delicious and the portions were generous"
                # Aspect: food -> delicious
                MockOpinion(
                    target=MockTarget("food", "positive", 0.9876, 0.0124),
                    assessments=[MockAssessment("delicious", "positive", 0.9876, 0.0124)]
                ),
                # Aspect: portions -> generous
                MockOpinion(
                    target=MockTarget("portions", "positive", 0.9712, 0.0288),
                    assessments=[MockAssessment("generous", "positive", 0.9712, 0.0288)]
                ),
                # Sentence 2: "but the service was painfully slow and the restaurant was noisy"
                # Aspect: service -> painfully slow
                MockOpinion(
                    target=MockTarget("service", "negative", 0.0231, 0.9769),
                    assessments=[MockAssessment("painfully slow", "negative", 0.0231, 0.9769)]
                ),
                # Aspect: restaurant -> noisy
                MockOpinion(
                    target=MockTarget("restaurant", "negative", 0.0412, 0.9588),
                    assessments=[MockAssessment("noisy", "negative", 0.0412, 0.9588)]
                )
            ]),
            "om2": MockAnalyzeSentimentResult("om2", "mixed", 0.5123, 0.0345, 0.4532, [
                MockSentence("Battery life on this phone is fantastic—easily two full days.", "positive", 0.9867, 0.0089, 0.0044),
                MockSentence("However, the camera quality is disappointing in low light.", "negative", 0.0312, 0.0534, 0.9154)
            ], opinions=[
                # Aspect: Battery life -> fantastic
                MockOpinion(
                    target=MockTarget("Battery life", "positive", 0.9912, 0.0088),
                    assessments=[MockAssessment("fantastic", "positive", 0.9912, 0.0088)]
                ),
                # Aspect: camera quality -> disappointing
                MockOpinion(
                    target=MockTarget("camera quality", "negative", 0.0156, 0.9844),
                    assessments=[MockAssessment("disappointing", "negative", 0.0156, 0.9844)]
                )
            ])
        }

    def analyze_sentiment(self, documents: List[Dict[str, str]], show_opinion_mining: bool = False, **kwargs) -> List[MockAnalyzeSentimentResult]:
        results = []
        for doc in documents:
            doc_id = doc.get("id")
            doc_text = doc.get("text", "")
            
            # Match by ID or look for keyword match if ID doesn't exist in DB
            if doc_id in self.mock_db:
                results.append(self.mock_db[doc_id])
            else:
                # Dynamic basic mock response for other documents
                text_lower = doc_text.lower()
                sentiment = "neutral"
                pos, neu, neg = 0.1, 0.8, 0.1
                
                if any(w in text_lower for w in ["great", "love", "excellent", "good", "amazing", "fantastic"]):
                    sentiment = "positive"
                    pos, neu, neg = 0.9, 0.08, 0.02
                elif any(w in text_lower for w in ["terrible", "bad", "slow", "disappointed", "worst"]):
                    sentiment = "negative"
                    pos, neu, neg = 0.02, 0.08, 0.9
                
                sentence_list = [MockSentence(doc_text, sentiment, pos, neu, neg)]
                results.append(MockAnalyzeSentimentResult(doc_id, sentiment, pos, neu, neg, sentence_list))
                
        # Simulate small network delay
        time.sleep(0.5)
        return results

# ==========================================
# RETRY LOGIC & UTILITIES
# ==========================================

def call_azure_with_retry(client: Union[TextAnalyticsClient, MockTextAnalyticsClient], documents: List[Dict[str, str]], show_opinion_mining: bool = True, max_retries: int = 3) -> List[Any]:
    """
    Sends requests to the Azure Language Service, with exponential backoff retry logic
    for transient errors (e.g., rate limits/429s, timeout errors).
    """
    backoff = 2
    for attempt in range(max_retries + 1):
        try:
            # Under live mode, using actual client. Under simulation, using mock client.
            results = client.analyze_sentiment(
                documents=documents, 
                show_opinion_mining=show_opinion_mining
            )
            return results
        except Exception as e:
            # Check if live SDK is being used and error is Azure-related
            is_transient = False
            status_code = getattr(e, "status_code", None)
            
            # HTTP 429 (Too Many Requests) or HTTP 5xx (Server Error) are retried
            if status_code in [429, 500, 503, 504]:
                is_transient = True
                
            if attempt < max_retries and (is_transient or "rate limit" in str(e).lower()):
                print(f"[WARNING] Request failed: {e}. Retrying in {backoff} seconds (Attempt {attempt+1}/{max_retries})...")
                time.sleep(backoff)
                backoff *= 2
            else:
                print(f"[ERROR] Max retries exceeded or non-transient error: {e}")
                raise e
    return []

# ==========================================
# RESPONSE PARSING
# ==========================================

def parse_sentiment_results(results: List[Any], show_opinion_mining: bool = True) -> List[Dict[str, Any]]:
    """
    Parses the Azure SDK response objects (or mock response objects) 
    into a serializable Python dict matching the expected results schema.
    """
    parsed_docs = []
    
    for result in results:
        if result.is_error:
            print(f"[ERROR] Document error: ID={result.id}")
            continue
            
        # 1. Base document info
        doc_data = {
            "id": result.id,
            "overall_label": result.sentiment,
            "confidence": {
                "positive": round(result.confidence_scores.positive, 4),
                "neutral": round(result.confidence_scores.neutral, 4),
                "negative": round(result.confidence_scores.negative, 4)
            },
            "sentences": [],
            "opinions": []
        }
        
        # 2. Sentence level analysis
        for sentence in result.sentences:
            sentence_data = {
                "text": sentence.text,
                "label": sentence.sentiment,
                "positive": round(sentence.confidence_scores.positive, 4),
                "neutral": round(sentence.confidence_scores.neutral, 4),
                "negative": round(sentence.confidence_scores.negative, 4)
            }
            doc_data["sentences"].append(sentence_data)
            
            # Check for opinions (some SDK versions use mined_opinions, others opinions)
            sentence_opinions = []
            if hasattr(sentence, "opinions") and sentence.opinions:
                sentence_opinions = sentence.opinions
            elif hasattr(sentence, "mined_opinions") and sentence.mined_opinions:
                sentence_opinions = sentence.mined_opinions

            if sentence_opinions:
                for opinion in sentence_opinions:
                    aspect = opinion.target.text
                    aspect_label = opinion.target.sentiment
                    assessments_list = []
                    
                    for assessment in opinion.assessments:
                        assessments_list.append({
                            "text": assessment.text,
                            "label": assessment.sentiment,
                            "positive": round(assessment.confidence_scores.positive, 4),
                            "negative": round(assessment.confidence_scores.negative, 4)
                        })
                        
                    doc_data["opinions"].append({
                        "aspect": aspect,
                        "aspect_label": aspect_label,
                        "assessments": assessments_list
                    })

        # Fallback to document-level opinions if opinion mining occurred at document-level in mock structure
        if hasattr(result, "opinions") and result.opinions and not doc_data["opinions"]:
            for opinion in result.opinions:
                aspect = opinion.target.text
                aspect_label = opinion.target.sentiment
                assessments_list = []
                
                for assessment in opinion.assessments:
                    assessments_list.append({
                        "text": assessment.text,
                        "label": assessment.sentiment,
                        "positive": round(assessment.confidence_scores.positive, 4),
                        "negative": round(assessment.confidence_scores.negative, 4)
                    })
                    
                doc_data["opinions"].append({
                    "aspect": aspect,
                    "aspect_label": aspect_label,
                    "assessments": assessments_list
                })
                
        parsed_docs.append(doc_data)
        
    return parsed_docs

# ==========================================
# REPORT GENERATION
# ==========================================

def generate_report(parsed_data: List[Dict[str, Any]], elapsed_time: float, is_simulated: bool) -> str:
    """
    Aggregates the parsed results to produce a comprehensive human-readable summary.
    """
    total = len(parsed_data)
    if total == 0:
        return "No documents processed."
        
    pos_count = sum(1 for d in parsed_data if d["overall_label"] == "positive")
    neu_count = sum(1 for d in parsed_data if d["overall_label"] == "neutral")
    neg_count = sum(1 for d in parsed_data if d["overall_label"] == "negative")
    mix_count = sum(1 for d in parsed_data if d["overall_label"] == "mixed")
    
    pos_pct = (pos_count / total) * 100
    neu_pct = (neu_count / total) * 100
    neg_pct = (neg_count / total) * 100
    mix_pct = (mix_count / total) * 100
    
    # Calculate average confidence
    avg_pos = sum(d["confidence"]["positive"] for d in parsed_data) / total
    avg_neu = sum(d["confidence"]["neutral"] for d in parsed_data) / total
    avg_neg = sum(d["confidence"]["negative"] for d in parsed_data) / total
    
    # Gather opinions
    opinions_summary = []
    for d in parsed_data:
        for op in d.get("opinions", []):
            aspect = op["aspect"]
            label = op["aspect_label"]
            evals = ", ".join([a["text"] for a in op["assessments"]])
            opinions_summary.append(f"  - Aspect: '{aspect}' is rated {label.upper()} (described as: {evals})")

    report_lines = [
        "======================================================================",
        "          AZURE COGNITIVE SERVICES SENTIMENT ANALYSIS REPORT          ",
        "======================================================================",
        f"Execution Mode : {'SIMULATION (Mock Azure Client)' if is_simulated else 'LIVE (Azure Cognitive Services)'}",
        f"Total Docs     : {total}",
        f"Elapsed Time   : {elapsed_time:.3f} seconds",
        "----------------------------------------------------------------------",
        "SENTIMENT DISTRIBUTION SUMMARY:",
        f"  * POSITIVE : {pos_count:3d} ({pos_pct:5.1f}%)",
        f"  * MIXED    : {mix_count:3d} ({mix_pct:5.1f}%)",
        f"  * NEUTRAL  : {neu_count:3d} ({neu_pct:5.1f}%)",
        f"  * NEGATIVE : {neg_count:3d} ({neg_pct:5.1f}%)",
        "----------------------------------------------------------------------",
        "AVERAGE CONFIDENCE SCORES:",
        f"  * Positive Confidence: {avg_pos:.4f}",
        f"  * Neutral Confidence : {avg_neu:.4f}",
        f"  * Negative Confidence: {avg_neg:.4f}",
        "----------------------------------------------------------------------",
        "ASPECT-BASED OPINION MINING (SAMPLES):"
    ]
    
    if opinions_summary:
        report_lines.extend(opinions_summary[:12])  # Limit display items in overview
        if len(opinions_summary) > 12:
            report_lines.append(f"  ... and {len(opinions_summary) - 12} other opinion aspects.")
    else:
        report_lines.append("  No aspects or opinions identified.")
        
    report_lines.append("======================================================================")
    
    return "\n".join(report_lines)

# ==========================================
# MAIN EXECUTION FLOW
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="Azure Sentiment Analysis Learning Script")
    parser.add_argument("--input", default="data/sample_reviews.json", help="Path to raw reviews JSON file")
    parser.add_argument("--output", default="output/results.json", help="Path to save sentiment output JSON")
    parser.add_argument("--report", default="output/summary_report.txt", help="Path to save text summary report")
    parser.add_argument("--mock", action="store_true", help="Force mock simulation mode")
    parser.add_argument("--endpoint", help="Azure Language Service Endpoint")
    parser.add_argument("--key", help="Azure Language Service API Key")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for Azure requests")
    parser.add_argument("--vault-url", help="Azure Key Vault URL to fetch the API Key")
    parser.add_argument("--secret-name", default="LanguageServiceApiKey", help="Azure Key Vault secret name containing the API key")
    
    args = parser.parse_args()
    
    # 1. Setup credentials and determine execution mode
    endpoint = args.endpoint or os.environ.get("AZURE_LANGUAGE_ENDPOINT")
    key = args.key or os.environ.get("AZURE_LANGUAGE_KEY")
    vault_url = args.vault_url or os.environ.get("AZURE_KEY_VAULT_URL")
    secret_name = args.secret_name or os.environ.get("AZURE_LANGUAGE_KEY_SECRET_NAME", "LanguageServiceApiKey")
    
    # Try fetching the API key from Azure Key Vault if URL is configured and key is not provided directly
    if vault_url and not key:
        print(f"[INFO] Azure Key Vault URL detected: {vault_url}. Attempting to retrieve secret '{secret_name}'...")
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            
            vault_credential = DefaultAzureCredential()
            secret_client = SecretClient(vault_url=vault_url, credential=vault_credential)
            retrieved_secret = secret_client.get_secret(secret_name)
            key = retrieved_secret.value
            print(f"[SUCCESS] Successfully retrieved Language Service API Key from Azure Key Vault.")
        except Exception as e:
            print(f"[WARNING] Failed to retrieve key from Azure Key Vault: {e}")
            print(f"[INFO] Will attempt local env key fallback.")
    
    is_simulated = True
    client = None
    
    if args.mock:
        print("[INFO] Mock mode explicitly requested via CLI.")
    elif not SDK_AVAILABLE:
        print("[WARNING] Azure AI Text Analytics SDK is not available. Falling back to Simulation Mode.")
    elif not endpoint or not key:
        print("[INFO] Azure credentials (endpoint and key) not fully resolved.")
        print("[INFO] Falling back to Simulation Mode for demonstration.")
    else:
        print(f"[INFO] Azure credentials detected. Setting up live connection...")
        try:
            credential = AzureKeyCredential(key)
            client = TextAnalyticsClient(endpoint=endpoint, credential=credential)
            is_simulated = False
            print("[SUCCESS] Live Azure Cognitive Services Client successfully initialized.")
        except Exception as e:
            print(f"[ERROR] Failed to initialize live client: {e}. Falling back to Simulation Mode.")
            is_simulated = True
            
    if is_simulated:
        client = MockTextAnalyticsClient()
        print("[INFO] Operating in SIMULATION mode. Responses are mock simulated structures.")
        
    # 2. Read input file
    if not os.path.exists(args.input):
        print(f"[ERROR] Input file '{args.input}' not found. Please create it or specify a valid path.")
        sys.exit(1)
        
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            documents = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse input JSON file: {e}")
        sys.exit(1)
        
    if not isinstance(documents, list):
        print("[ERROR] Input format must be a JSON array of documents.")
        sys.exit(1)
        
    print(f"[INFO] Loaded {len(documents)} documents for sentiment analysis.")
    
    # 3. Batch process and execute analysis
    start_time = time.time()
    all_parsed_results = []
    
    # Slice documents into batches (Azure Language Service limit: standard is 10 docs/request)
    for i in range(0, len(documents), args.batch_size):
        batch = documents[i : i + args.batch_size]
        batch_docs = []
        
        for doc in batch:
            if "id" not in doc or "text" not in doc:
                print(f"[WARNING] Skipping document at index {documents.index(doc)}: must contain 'id' and 'text'")
                continue
            batch_docs.append({"id": doc["id"], "text": doc["text"]})
            
        if not batch_docs:
            continue
            
        print(f"[INFO] Analyzing batch {i // args.batch_size + 1} ({len(batch_docs)} documents)...")
        
        try:
            # Execute request with retry mechanism
            batch_results = call_azure_with_retry(client, batch_docs, show_opinion_mining=True)
            # Parse responses
            parsed_batch = parse_sentiment_results(batch_results, show_opinion_mining=True)
            all_parsed_results.extend(parsed_batch)
        except Exception as e:
            print(f"[FATAL ERROR] Batch processing failed: {e}")
            sys.exit(1)
            
    elapsed = time.time() - start_time
    print(f"[SUCCESS] Analyzed {len(all_parsed_results)} documents in {elapsed:.3f} seconds.")
    
    # 4. Save structured JSON output
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(all_parsed_results, f, indent=2, ensure_ascii=False)
        print(f"[SUCCESS] JSON results saved to '{args.output}'")
    except Exception as e:
        print(f"[ERROR] Failed to write JSON output: {e}")
        
    # 5. Generate and write summary report
    report_content = generate_report(all_parsed_results, elapsed, is_simulated)
    
    # Print to console
    print("\n" + report_content + "\n")
    
    # Write to report file
    try:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"[SUCCESS] Text report saved to '{args.report}'")
    except Exception as e:
        print(f"[ERROR] Failed to write text report: {e}")

if __name__ == "__main__":
    main()
