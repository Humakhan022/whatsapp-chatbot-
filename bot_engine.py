import os
import json
import csv
import re
import math
from difflib import SequenceMatcher
from datetime import datetime

class WhatsAppBotEngine:
    def __init__(self, dataset_path=None):
        self.dataset_path = dataset_path
        self.bot_name = "NovaTech Assistant"
        self.bot_tagline = "Official Sales & Support Bot"
        self.category = "E-Commerce & Tech Support"
        self.welcome_message = "Hello! 👋 How can I help you today?"
        self.fallback_message = "I'm sorry, I didn't quite catch that. Here are some topics I can help with:"
        self.default_quick_replies = ["Track Order", "Best Laptops", "Return Policy", "Store Hours"]
        self.knowledge_base = []
        self.active_dataset_id = "novatech_store"
        
        # Inverted index & IDF weights
        self.idf_weights = {}
        self.doc_vectors = []
        
        # Session state memory (simulating WhatsApp phone number sessions)
        self.sessions = {}
        
        # Analytics counters
        self.analytics = {
            "total_messages": 0,
            "matched_queries": 0,
            "fallback_queries": 0,
            "intents_triggered": {}
        }

        if dataset_path and os.path.exists(dataset_path):
            self.load_dataset(dataset_path)
        else:
            default_path = os.path.join(os.path.dirname(__file__), "data", "novatech_store.json")
            if os.path.exists(default_path):
                self.load_dataset(default_path)

    def _tokenize(self, text):
        if not text:
            return []
        text = text.lower()
        tokens = re.findall(r'[a-z0-9\-]+', text)
        stopwords = {
            "a", "an", "the", "and", "or", "is", "are", "was", "were", "to", "in", 
            "at", "of", "for", "on", "with", "about", "by", "do", "does", "did", 
            "i", "you", "my", "your", "we", "our", "me", "can", "could", "would", 
            "should", "it", "what", "how", "tell", "show", "give", "please", "want", 
            "know", "need", "any", "some", "there", "their", "have", "has", "get"
        }
        filtered = [t for t in tokens if t not in stopwords]
        return filtered if filtered else tokens

    def _compute_idf(self):
        doc_count = len(self.knowledge_base)
        if doc_count == 0:
            return
        doc_freq = {}
        for entry in self.knowledge_base:
            seen_tokens = set()
            for pattern in entry.get("patterns", []):
                seen_tokens.update(self._tokenize(pattern))
            seen_tokens.update(self._tokenize(entry.get("intent", "")))
            seen_tokens.update(self._tokenize(entry.get("question", "")))
            for token in seen_tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1

        self.idf_weights = {
            token: math.log((1 + doc_count) / (1 + count)) + 1.0
            for token, count in doc_freq.items()
        }

    def load_dataset(self, file_path):
        """Loads a dataset from JSON or CSV"""
        self.dataset_path = file_path
        filename = os.path.basename(file_path).lower()
        self.active_dataset_id = os.path.splitext(os.path.basename(file_path))[0]
        
        if filename.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._parse_json_dataset(data)
        elif filename.endswith(".csv"):
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self._parse_csv_dataset(rows, title=os.path.splitext(os.path.basename(file_path))[0])
        
        self._compute_idf()
        return True

    def _parse_json_dataset(self, data):
        self.bot_name = data.get("bot_name", "AI WhatsApp Bot")
        self.bot_tagline = data.get("bot_tagline", "Automated Knowledge Assistant")
        self.category = data.get("category", "General")
        self.welcome_message = data.get("welcome_message", "Hello! How can I assist you?")
        self.fallback_message = data.get("fallback_message", "I didn't quite get that. Here are some topics I can answer:")
        self.default_quick_replies = data.get("quick_replies", ["Help", "About", "Contact"])
        self.knowledge_base = data.get("knowledge_base", [])

    def _parse_csv_dataset(self, rows, title="Custom Dataset"):
        self.bot_name = f"{title.capitalize()} Bot"
        self.bot_tagline = "CSV Powered Knowledge Bot"
        self.category = "Custom FAQ"
        self.welcome_message = f"Hello! 👋 Welcome to *{self.bot_name}*.\n\nAsk me anything from our knowledge base!"
        self.fallback_message = "I couldn't find an exact answer for that question. Here are some topics you can explore:"
        
        kb = []
        all_replies = set()
        for idx, row in enumerate(rows):
            q = row.get("question", "").strip()
            a = row.get("answer", "").strip()
            cat = row.get("category", "General").strip()
            qr = row.get("quick_replies", "").strip()
            if not q or not a:
                continue
            
            patterns = [q.lower()]
            clean_q = re.sub(r'[^\w\s]', '', q.lower())
            if clean_q not in patterns:
                patterns.append(clean_q)
            
            if "keywords" in row and row["keywords"]:
                for kw in row["keywords"].split(";"):
                    if kw.strip():
                        patterns.append(kw.strip().lower())
            
            quick_list = [r.strip() for r in qr.split(";") if r.strip()] if qr else [q[:20]]
            all_replies.update(quick_list)
            
            kb.append({
                "id": f"kb_csv_{idx+1}",
                "intent": f"faq_{idx+1}",
                "question": q,
                "category": cat,
                "patterns": patterns,
                "response": a,
                "quick_replies": quick_list[:3]
            })

        self.knowledge_base = kb
        self.default_quick_replies = list(all_replies)[:5] if all_replies else ["Help", "Info"]

    def set_custom_dataset(self, data_dict):
        """Sets dataset directly from dictionary (e.g. from UI upload or edit)"""
        self._parse_json_dataset(data_dict)
        self.active_dataset_id = "custom"
        self._compute_idf()

    def _calculate_similarity(self, query, query_tokens, pattern):
        """Calculates multi-dimensional similarity between query and pattern"""
        clean_pat = pattern.lower().strip()
        clean_q = query.lower().strip()
        
        # 1. Exact match
        if clean_q == clean_pat:
            return 1.0
            
        # 2. Substring match
        if clean_pat in clean_q or clean_q in clean_pat:
            len_ratio = min(len(clean_q), len(clean_pat)) / max(len(clean_q), len(clean_pat))
            return 0.85 + 0.14 * len_ratio

        # 3. Whole query SequenceMatcher
        fuzzy_ratio = SequenceMatcher(None, clean_q, clean_pat).ratio()
        if fuzzy_ratio > 0.85:
            return 0.88 * fuzzy_ratio

        pat_tokens = self._tokenize(clean_pat)
        if not query_tokens or not pat_tokens:
            return fuzzy_ratio * 0.7

        # 4. Token-by-token alignment with fuzzy match & IDF weighting
        # For each pattern token, find the best match in query tokens
        pat_match_scores = []
        for pt in pat_tokens:
            best_t_score = 0.0
            for qt in query_tokens:
                if pt == qt:
                    best_t_score = 1.0
                    break
                elif pt in qt or qt in pt:
                    best_t_score = max(best_t_score, 0.85)
                else:
                    t_ratio = SequenceMatcher(None, pt, qt).ratio()
                    if t_ratio > 0.72:
                        best_t_score = max(best_t_score, t_ratio)
            pat_match_scores.append(best_t_score)

        if pat_match_scores:
            avg_pat_score = sum(pat_match_scores) / len(pat_match_scores)
            min_pat_score = min(pat_match_scores)
            
            # If all pattern tokens were matched strongly (e.g. "retun" & "polic")
            if min_pat_score >= 0.70:
                return min(0.92, 0.80 + 0.20 * avg_pat_score)
            
            if avg_pat_score >= 0.60:
                return min(0.85, 0.50 + 0.35 * avg_pat_score)

        # 5. Jaccard token overlap with IDF
        common_tokens = set(query_tokens).intersection(set(pat_tokens))
        if common_tokens:
            total_score = sum(self.idf_weights.get(t, 1.0) for t in common_tokens)
            max_possible = sum(self.idf_weights.get(t, 1.0) for t in set(query_tokens).union(set(pat_tokens)))
            jaccard_weighted = total_score / max(max_possible, 1.0)
            return max(0.50 + 0.40 * jaccard_weighted, fuzzy_ratio)

        return fuzzy_ratio * 0.5

    def process_message(self, user_text, session_id="default_user"):
        """
        Main query processing logic. Returns a structured WhatsApp response object.
        """
        self.analytics["total_messages"] += 1
        clean_input = user_text.strip()
        if not clean_input:
            return {
                "reply": self.welcome_message,
                "confidence": 1.0,
                "matched_intent": "welcome",
                "quick_replies": self.default_quick_replies,
                "timestamp": datetime.now().strftime("%I:%M %p")
            }

        # Initialize or retrieve session state
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],
                "user_name": None,
                "last_intent": None
            }
        session = self.sessions[session_id]

        # Check for dynamic entity / Order tracking: ORD-XXXX
        order_match = re.search(r'\b(ord[-\s]?\d{3,6})\b', clean_input, re.IGNORECASE)
        if order_match:
            order_id = order_match.group(1).upper().replace(" ", "-")
            if not order_id.startswith("ORD-"):
                order_id = f"ORD-{order_id}"
            
            self.analytics["matched_queries"] += 1
            self.analytics["intents_triggered"]["dynamic_order_tracking"] = (
                self.analytics["intents_triggered"].get("dynamic_order_tracking", 0) + 1
            )
            
            # Dynamic simulated realistic tracking status
            tracking_msg = (
                f"📦 *Live WhatsApp Order Tracking*\n\n"
                f"• *Order ID*: `{order_id}`\n"
                f"• *Status*: 🚚 *In Transit - Out for Delivery*\n"
                f"• *Carrier*: NovaExpress Logistics (Tracking #NX-8839201)\n"
                f"• *Estimated Arrival*: Today by *4:30 PM*\n"
                f"• *Delivery Address*: Verified customer address\n\n"
                f"Driver is currently 4 stops away! You will receive a WhatsApp notification when delivered."
            )
            return {
                "reply": tracking_msg,
                "confidence": 0.99,
                "matched_intent": "order_tracking_active",
                "quick_replies": ["Track Another Order", "Change Delivery Address", "Talk to Agent"],
                "timestamp": datetime.now().strftime("%I:%M %p")
            }

        query_tokens = self._tokenize(clean_input)

        best_score = 0.0
        best_entry = None
        best_pattern = ""

        for entry in self.knowledge_base:
            patterns = entry.get("patterns", [])
            for pattern in patterns:
                score = self._calculate_similarity(clean_input, query_tokens, pattern)
                if score > best_score:
                    best_score = score
                    best_entry = entry
                    best_pattern = pattern

        CONFIDENCE_THRESHOLD = 0.42

        if best_entry and best_score >= CONFIDENCE_THRESHOLD:
            intent = best_entry.get("intent", "general")
            self.analytics["matched_queries"] += 1
            self.analytics["intents_triggered"][intent] = (
                self.analytics["intents_triggered"].get(intent, 0) + 1
            )
            session["last_intent"] = intent
            
            reply_text = best_entry.get("response", "")
            quick_replies = best_entry.get("quick_replies", self.default_quick_replies)

            # If confidence is moderate (0.42 to 0.65), suggest related questions
            if 0.42 <= best_score < 0.65:
                # Find secondary matches for suggestions
                other_suggestions = [
                    e.get("patterns", [""])[0] 
                    for e in self.knowledge_base 
                    if e.get("id") != best_entry.get("id")
                ][:2]
                if other_suggestions:
                    suggestion_pills = [s.title() for s in other_suggestions if s]
                    quick_replies = list(dict.fromkeys(quick_replies + suggestion_pills))[:4]

            return {
                "reply": reply_text,
                "confidence": round(best_score, 2),
                "matched_intent": intent,
                "matched_pattern": best_pattern,
                "quick_replies": quick_replies,
                "timestamp": datetime.now().strftime("%I:%M %p")
            }
        else:
            # Fallback
            self.analytics["fallback_queries"] += 1
            fallback_text = f"{self.fallback_message}\n\n" + "\n".join([f"• {qr}" for qr in self.default_quick_replies[:4]])
            return {
                "reply": fallback_text,
                "confidence": round(best_score, 2),
                "matched_intent": "fallback_unrecognized",
                "matched_pattern": None,
                "quick_replies": self.default_quick_replies,
                "timestamp": datetime.now().strftime("%I:%M %p")
            }

    def get_dataset_summary(self):
        """Returns metadata about the active dataset"""
        return {
            "active_dataset_id": self.active_dataset_id,
            "bot_name": self.bot_name,
            "bot_tagline": self.bot_tagline,
            "category": self.category,
            "total_intents": len(self.knowledge_base),
            "total_patterns": sum(len(e.get("patterns", [])) for e in self.knowledge_base),
            "quick_replies": self.default_quick_replies,
            "welcome_message": self.welcome_message,
            "fallback_message": self.fallback_message,
            "knowledge_base": self.knowledge_base
        }

    def add_or_update_entry(self, entry_data):
        """Adds a new QA entry or updates existing one"""
        entry_id = entry_data.get("id")
        if not entry_id:
            entry_id = f"kb_custom_{len(self.knowledge_base) + 1}"
            entry_data["id"] = entry_id

        # Format patterns
        if isinstance(entry_data.get("patterns"), str):
            patterns = [p.strip().lower() for p in entry_data["patterns"].split(",") if p.strip()]
            entry_data["patterns"] = patterns

        if isinstance(entry_data.get("quick_replies"), str):
            replies = [r.strip() for r in entry_data["quick_replies"].split(",") if r.strip()]
            entry_data["quick_replies"] = replies

        # Check existing
        existing_idx = None
        for i, entry in enumerate(self.knowledge_base):
            if entry.get("id") == entry_id:
                existing_idx = i
                break

        if existing_idx is not None:
            self.knowledge_base[existing_idx] = entry_data
        else:
            self.knowledge_base.append(entry_data)

        self._compute_idf()
        return entry_data

    def delete_entry(self, entry_id):
        """Removes an entry from the knowledge base"""
        initial_len = len(self.knowledge_base)
        self.knowledge_base = [e for e in self.knowledge_base if e.get("id") != entry_id]
        if len(self.knowledge_base) < initial_len:
            self._compute_idf()
            return True
        return False
