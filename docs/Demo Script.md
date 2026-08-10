# 🎤 Chameleon AI — Hackathon Demo Script
## FlowZint AI Hackathon 2026

**Total Time: 3-4 minutes**
**Speaker: Daksh**

---

## OPENING (30 sec)

> "Imagine aap ek business owner ho. Hazaron customers roz aapke support team se baat karte hain. Kuch khush hain, kuch frustrated hain — aur kuch itne angry hain ki deal toot jaayegi. Problem yeh hai ki aapki team real-time mein yeh detect nahi kar sakti.
>
> Aaj hum present karte hain — **Chameleon AI** — ek real-time emotion intelligence platform jo har customer message ko analyze karta hai, emotion detect karta hai, aur automatically sahi action leta hai."

---

## PROBLEM STATEMENT (30 sec)

> "75% businesses ke paas koi system nahi hai jo customer frustration real-time mein detect kare.
>
> Result? Angry customers chale jaate hain. Happy customers ko upsell miss ho jaata hai. Aur support agents ko pata hi nahi chalta ki kab escalate karna tha.
>
> **Chameleon AI yeh sab solve karta hai.**"

---

## LIVE DEMO (2 min)

### Step 1 — Dashboard dikhao
> "Yeh hai humara live dashboard. Upar left mein aap dekh sakte ho humara 3D AI robot — jo real-time mein customer ki emotion reflect karta hai. Live emotion graph mein score continuously update hota hai."

### Step 2 — Happy customer
*Type: "Bahut acha service hai, shukriya! Mujhe aur products chahiye!"*

> "Dekho — score 0.9 — green zone mein. AI ne detect kiya ki customer khush hai. Action: UPSELL. Bot ne automatically special offer bhej diya. Graph bhi upar gaya."

### Step 3 — Angry customer  
*Type: "Yeh kya bakwaas service hai! Mera paisa wapas karo!"*

> "Ab ek frustrated customer. Score 0.0 — ekdum red zone. Aur dekho kya hua —"

*🚨 Alert popup aata hai*

> "**ALERT — HUMAN AGENT REQUIRED.** Real-time mein system ne detect kiya, bot ne empathetic reply diya, aur human agent ko alert aa gaya. Yeh sab hua — 1 second se bhi kam mein."

### Step 4 — History
*Browser mein `localhost:8000/history` open karo*

> "Aur yeh sab conversations automatically SQLite database mein save ho rahe hain — full history, timestamps ke saath."

---

## TECH STACK (30 sec)

> "Under the hood:
> - **Groq + LLaMA 3.3 70B** — free, ultra-fast AI inference
> - **Python FastAPI** — WebSocket for real-time communication  
> - **React + Recharts** — live graph dashboard
> - **SQLite** — conversation history
>
> Poora system **production-ready architecture** pe built hai — scale karna ho toh sirf DB aur WebSocket layer replace karo."

---

## CLOSING (30 sec)

> "Chameleon AI sirf ek chatbot nahi hai. Yeh ek **predictive intelligence layer** hai jo kisi bhi business ke customer service pe laga sakte ho.
>
> Innovation, scalability, real-world problem solving, technical architecture — humne FlowZint ke har criteria ko address kiya hai.
>
> **Chameleon AI — Emotion ko samjho. Customer ko rakho.**
>
> Thank you!"

---

## ⚠️ Demo Tips

- Server pehle se chalu rakho (`uvicorn main:app --reload`)
- Frontend bhi ready rakho (`npm run dev`)
- Pehle happy message bhejo, phir angry — graph ka contrast dikhega
- Alert popup ke time pe thoda ruko — dramatic effect ke liye
- History endpoint browser mein kholo — judges data dekh ke impress honge

---

## 🔥 Possible Judge Questions

**Q: OpenAI ki jagah Groq kyun?**
> "Groq free hai aur GPT-4o se 10x fast hai inference mein. Hackathon ke liye perfect."

**Q: Real production mein scale kaise hoga?**
> "WebSocket rooms per session, PostgreSQL for DB, aur Groq paid tier. Architecture already stateless hai."

**Q: Sirf customer service ke liye hai?**
> "Nahi — HR feedback, social media monitoring, product reviews — kahi bhi text-based emotion detection chahiye wahan use kar sakte hain."

**Q: Hindi ke alawa aur languages?**
> "LLaMA 3.3 multilingual hai — prompt change karo, koi bhi language support ho jaayegi."