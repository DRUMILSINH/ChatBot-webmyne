from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied, ValidationError
import json
from chatbot.pipeline import crawl_and_embed
from chatbot.utils import make_local_chain
from .models import PersonalInfo
from .models import ClickedURL
from chat.security import validate_crawl_url
import sys
import os
import re
from textblob import TextBlob
import difflib
import random
import uuid
import time
from .models import ChatLog


# Add path to the chatbot folder (parent directory of chatbot_ui)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, 'chatbot'))

def is_gibberish(text):
    clean_text = text.strip()

    if len(clean_text) < 8:
        return True

    if not re.search(r"[aeiou]", clean_text.lower()):
        return True

    # Only reject if there are too many weird characters
    special_chars = re.findall(r"[^a-zA-Z0-9\s.,?!'-]", clean_text)
    if len(special_chars) > 3:
        return True

    # Reject very long single-word inputs
    if len(clean_text.split()) == 1 and len(clean_text) > 8:
        return True

    return False
#  Safer word-level spelling correction
def correct_spelling(text):
    corrected = []
    for word in text.split():
        if len(word) <= 6 and word.isalpha():
            corrected.append(str(TextBlob(word).correct()))
        else:
            corrected.append(word)
    return " ".join(corrected)

def chat_view(request):
    vector_id = "webmyne"  # or get it from query param/session/etc
    cache_file = f"db/{vector_id}/crawled_data.json"
    crawl_urls = []

    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            pages = json.load(f)
            crawl_urls = [page.get("metadata", {}).get("url") for page in pages if page.get("metadata", {}).get("url") ]

    return render(request, "chat/chat.html", {
        "crawl_urls": crawl_urls,
        "vector_id": vector_id,
    })

def get_device_type(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()
    if 'mobile' in ua:
        return 'mobile'
    elif 'tablet' in ua:
        return 'tablet'
    else:
        return 'desktop'


@csrf_exempt
def chatbot_query(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

    try:
        data = json.loads(request.body)
        original_query = data.get("query", "").strip()
        vector_id = data.get("vector_id", "").strip()

        if not original_query or not vector_id:
            return JsonResponse({"error": "Missing 'query' or 'vector_id'."}, status=400)

        user_input = request.POST.get('user_input', original_query)
        vector_id = request.POST.get('vector_id', vector_id)  # tenant/company
        name = request.POST.get('name', '')  # optional fields from form
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')

        session_id = request.session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['session_id'] = session_id

        query = original_query.lower()  #  Normalize to lowercase for case-insensitive


        # ✨ Handle small talk or greetings
        small_talk_responses = {
            "name": ["Hi there! I your AI bot, available for instant clarification!."],
            "hi": ["Hi there! How can I help you today?"],
            "what's up": ["Hey! All good here — what's on your end? 😄"],
            "hello": ["Hello, How are you?","Hello! What would you like to know about the company?"],
            "hey": ["Hey! Ask me anything about the website."],
            "how are you": ["I'm awesome, thanks for asking! 😊", "As always, Amazing!!!"],
            "bye" :["It's a pleasure talking to you 😊", "Let me know when you are back!!"],
            "that's great": ["I am glad to hear that 😊"],
            "amazing": ["I am glad to hear that 😊"],
            "thank you":["My pleasure, happy to help you!!!"],
            "Contact details": ["Email ID: creativebiz@webmyne.com, Bussiness Inquiry: +91 9898490360 "],
            "good morning": ["Hey, how you doin!!?","Good morning! How can I assist you in answering your query regarding company?"],
            "good evening": ["Good evening! What would you like to know about the company?","A very good evening!!"],
        }
        ## Exact match
        for phrase, reply in small_talk_responses.items():
            if re.search(rf'\b{re.escape(phrase)}\b', query):
                res= random.choice(reply)
                personal_info, _ = PersonalInfo.objects.get_or_create(
                    session_id=session_id,
                    defaults={
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "device_type": get_device_type(request)
                    }
                )
                #  Save chat log
                start = time.time()
                end = time.time()
                ChatLog.objects.create(
                    session=personal_info,
                    # request_id=str(uuid.uuid4()),
                    user_query=user_input,

                    # start=time.time(),
                    response=res, # or resp, resp_, fallback, etc.
                    # end = time.time(),
                    response_time = round(end - start, 3),
                    # response_time=0.0,  # or 0.0 for small talk/gibberish
                    vector_id=vector_id
                )
                return JsonResponse({"answer": res, "sources": []}, status=200)
        ## fuzzy match
        match = difflib.get_close_matches(query, small_talk_responses.keys(), n=1, cutoff=0.55)
        if match:
            resp = random.choice(small_talk_responses[match[0]])
            personal_info, _ = PersonalInfo.objects.get_or_create(
                session_id=session_id,
                defaults={
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "device_type": get_device_type(request)
                }
            )
            start = time.time()
            end = time.time()
            ChatLog.objects.create(
                session=personal_info,
                # request_id=str(uuid.uuid4()),
                user_query=user_input,

                # start=time.time(),
                response=resp,
                # end=time.time(),
                response_time=round(end - start, 3),
                # response_time=0.0,
                vector_id=vector_id
            )
            return JsonResponse({"answer": resp, "sources": []}, status=200)

        if is_gibberish(query):
            resp_ = "I'm sorry, I couldn't understand your question. Could you please rephrase it clearly?"
            personal_info, _ = PersonalInfo.objects.get_or_create(
                session_id=session_id,
                defaults={
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "device_type": get_device_type(request)
                }
            )
            start = time.time()
            end = time.time()
            ChatLog.objects.create(
                session=personal_info,
                # request_id=str(uuid.uuid4()),
                user_query=user_input,

                # start=time.time(),
                response=resp_,
                # end=time.time(),
                response_time=round(end - start, 3),
                # response_time=0.0,
                vector_id=vector_id
            )
            return JsonResponse({
                "answer": resp_,
                "sources": []
            }, status=200)

        corrected_query = correct_spelling(query)

        # Start timing
        start = time.time()
        chain = make_local_chain(vector_id)
        result = chain.invoke({"query": corrected_query, "context": ""})
        end = time.time()
        response_time = round(end - start, 3)


#------
        answer = result["result"]
        source_docs = result.get("source_documents", [])
###################

        seen_path = f"db/{vector_id}/seen_urls.json"
        found_path = f"db/{vector_id}/found_urls.json"
        os.makedirs(os.path.dirname(seen_path), exist_ok=True)
        os.makedirs(os.path.dirname(found_path), exist_ok=True)

        try:
            with open(seen_path, "r", encoding="utf-8") as f:
                seen_urls = set(json.load(f))
        except:
            seen_urls = set()

        try:
            with open(found_path, "r", encoding="utf-8") as f:
                found_urls = set(json.load(f))
        except:
            found_urls = set()

        for doc in source_docs:
            page_title = doc.metadata.get("title", "").strip()
            true_url = doc.metadata.get("url", "").strip()
            if page_title and true_url:
                pattern = re.escape(page_title)
                replacement = f"[{page_title}]({true_url})"
                answer = re.sub(pattern, replacement, answer)

        def clean_hallucinated_links(text, valid_urls):  # [text](hallucinated url)
            def repl(match):
                url = match.group(2)
                return match.group(1) if url not in valid_urls else match.group(0)

            return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', repl, text)

        valid_urls = {doc.metadata.get("url", "") for doc in source_docs}
        answer = clean_hallucinated_links(answer, valid_urls)
        ###############

        def remove_plain_fake_urls(text, valid_urls):   #(visit: hallucinated url)
            url_pattern = re.compile(r"(https?://[^\s)]+)")

            def replacer(match):
                url = match.group(1)
                if url in valid_urls:
                    return url
                return ""  # Remove hallucinated raw URL

            return url_pattern.sub(replacer, text)

        #  Remove raw URLs not in the crawled dataset
        answer = remove_plain_fake_urls(answer, valid_urls)
        ################
        keywords = ["certification", "experience", "solution", "service", "development",
                    "company","webmyne"]

        def contains_keyword(answer: str) -> bool:
            answer_lower = answer.lower()

            #  Direct match using regex (word boundary)
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}\b", answer_lower):
                    return True

            #  Fuzzy match with difflib (e.g., typos like "servces")
            words_in_answer = re.findall(r'\b\w+\b', answer_lower)
            for word in words_in_answer:
                match = difflib.get_close_matches(word, keywords, n=1, cutoff=0.55)
                if match:
                    return True

            return False

        #  Fallback if no documents or too generic
        if not source_docs or not contains_keyword(answer):
            fallback = "Sorry, I couldn't find relevant information. Please rephrase your query."
            personal_info, _ = PersonalInfo.objects.get_or_create(
                session_id=session_id,
                defaults={
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "device_type": get_device_type(request)
                }
            )
            ChatLog.objects.create(
                session=personal_info,
                # request_id=str(uuid.uuid4()),
                user_query=user_input,
                response=fallback,
                response_time=response_time,
                vector_id=vector_id
            )
            return JsonResponse({
                "answer": fallback,
                "response": fallback,
                "sources": []
            }, status=200)

        sources_with_note = []
        for doc in source_docs:
            url = doc.metadata.get("url", "")
            # tag = ""
            if url in seen_urls:
                note = "verified"
            elif url in found_urls:
                note = " Discovered but not crawled yet"
            else:
                note = "Possibly hallucination"

            sources_with_note.append({
                "url": url,
                "chunk_id": doc.metadata.get("chunk_id"),
                "md5": doc.metadata.get("md5"),
                "content": doc.page_content[:500],
                "note": note
            })
        #  Save to PostgreSQL
        personal_info, _ = PersonalInfo.objects.get_or_create(
            session_id=session_id,
            defaults={
                "name": name,
                "email": email,
                "phone": phone,
                "device_type": get_device_type(request)
            }
        )
        ChatLog.objects.create(
            session=personal_info,
            # request_id=str(uuid.uuid4()),
            user_query=user_input,
            response=answer,
            response_time=response_time,
            vector_id=vector_id
        )

        #--------------
        response = {
            # "answer": result["result"],
            "answer": answer,
            "sources": sources_with_note

        }
        return JsonResponse(response, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def log_clicked_url(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            url = data.get("url", "").strip()
            session_id = request.session.get("session_id")

            if not url or not session_id:
                return JsonResponse({"error": "Missing URL or session"}, status=400)

            personal_info = PersonalInfo.objects.filter(session_id=session_id).first()
            if not personal_info:
                return JsonResponse({"error": "No PersonalInfo for session"}, status=404)

            ClickedURL.objects.create(
                session=personal_info,
                url=url
            )
            return JsonResponse({"status": "success"}, status=200)

        except (ValidationError, PermissionDenied) as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method allowed"}, status=405)

@csrf_exempt
def save_user_info(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed."}, status=405)

    try:
        data = json.loads(request.body)
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()

        session_id = request.session.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['session_id'] = session_id

        # device_type = get_device_type(request)

        personal_info, created = PersonalInfo.objects.get_or_create(
            session_id=session_id,
            defaults={"name": name, "email": email, "phone": phone} #, "device_type": device_type}
        )

        if not created:
            # Update if already exists
            personal_info.name = name or personal_info.name
            personal_info.email = email or personal_info.email
            personal_info.phone = phone or personal_info.phone
            personal_info.save()

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def get_user_name(request):
    session_id = request.session.get("session_id")
    if session_id:
        personal_info = PersonalInfo.objects.filter(session_id=session_id).first()
        if personal_info and personal_info.name:
            return JsonResponse({"name": personal_info.name or "", "email": personal_info.email or "",
                "phone": personal_info.phone or ""})
    return JsonResponse({"name": "You", "email": "", "phone": ""})


@csrf_exempt
def crawl_and_embed_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            url = data.get('url')
            vector_id = data.get('vector_id')

            if not url or not vector_id:
                return JsonResponse({"error": "Missing 'url' or 'vector_id' in request"}, status=400)

            validate_crawl_url(url, vector_id)
            result = crawl_and_embed(url=url, vector_id=vector_id)
            return JsonResponse(result)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method is allowed"}, status=405)
# Create your views here.
