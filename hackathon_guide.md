# 🧠 Déjà Hackathon Pitch & Demo Guide: Winning National Hackathon Strategy

This guide is structured to help you score the maximum marks across all evaluation categories for **Déjà** at the national hackathon. It is written to be engaging, high-impact, and accessible even if you do not have a deep background in technical systems.

---

## 🏆 Rubric Mapping Strategy: Scoring 100/100

| Category | Score | How Déjà Wins |
| :--- | :---: | :--- |
| **Relevance to SDG(s)** | **10** | **SDG 3 (Good Health & Well-Being)**: Direct response to the global mental health epidemic, academic/occupational burnout, and memory degradation. **SDG 9 (Industry, Innovation & Infrastructure)**: Hybrid serverless local-to-cloud graph infrastructure. |
| **Innovation & Uniqueness** | **20** | Marrying **exact time-series chronological databases** (PostgreSQL/Supabase) with **semantic knowledge-graph mapping** (Cognee). Blindspots engine detects conceptual vs. chronological gaps. GDPR-compliant target conceptual pruning (`cognee.forget()`). |
| **Impact** | **20** | Bridges years of abstract, unstructured human journal noise into actionable behavioral insights. Solves query latency, reducing recall times from **~10s to ~1.5s** (10× faster) via a custom hybrid shortcut. |
| **Feasibility & Sustainability**| **20** | **Offline-first local model** (local SQLite & LanceDB) ensures zero provider hosting costs for the Free Tier. **Serialized Async Queue** in FastAPI prevents database lock contention, proving enterprise readiness. |
| **Project Demonstration** | **20** | A live, step-by-step walkthrough showing immediate ingestion, multi-year correlation retrieval (meditation vs. coding flow), blindspot paradox detection, and conceptual sanctuary pruning. |
| **Q&A Prep** | **10** | Clear, non-technical explanations for complex backend behaviors (concurrency, vector similarity, graph routing). |

---

## ⏱️ Pitch Timeline (Total: 5 Minutes)

```mermaid
gantt
    title Hackathon Presentation Timeline (5 Minutes)
    dateFormat  m:s
    axisFormat %M:%S
    section Pitch
    Slide 1-3: The Hook & Problem      :00:00, 00:45
    Slide 4-5: UVP & Architecture       :00:45, 01:30
    section Live Demo
    Live Demo: Slate & Oracle         :01:30, 02:45
    Live Demo: Blindspots & Sanctuary :02:45, 03:45
    section Wrap up
    Slide 7: Business Model & SDGs    :03:45, 04:15
    Q&A Buffer / Conclusion           :04:15, ## 🎤 The 5-Minute Script: Slide by Slide

### ⏱️ 0:00 - 0:45 | Slide 1-3: The Hook & The Problem (SDG 3 Alignment)
**[Presenter stands confidently. Show Slide 1: Title Cover]**
*   **Script:** "Good morning, judges. Most of us who write in journals do it to solve a fundamental human challenge: to make sense of our lives, our moods, and our habits. We journal when we're stressed about placements, when we have a productive day coding, or when we notice our mental energy dipping. But if I ask you right now: *What unseen lifestyle triggers are dragging you into burnout?* or *When exactly did you start losing track of your career and wellness goals?* You wouldn't know. The answers are locked in hundreds of pages of unread, static text. Journals have become cemeteries of thoughts. This directly links to **SDG 3: Good Health & Well-Being**—we write to remember, but we lack the tools to search, analyze, and recover our own mental state."

**[Transition to Slide 2: Problem Statement]**
*   **Script:** "Traditional journals lack intelligent cross-referencing, and standard AI tools have no long-term memory of your behavior. That’s why we built **Déjà** — a Cognee-powered cognitive sanctuary that reconstructs unstructured text files into a queryable semantic brain. It acts as an external memory layer, helping you reveal hidden habits, map emotional cycles, and trace personal growth across years of life."

---

### ⏱️ 0:45 - 01:30 | Slide 4-5: Innovation, Uniqueness & Architecture
**[Transition to Slide 4: Unique Value Proposition]**
*   **Script:** "What makes Déjà an **Innovation & Uniqueness** leader is its first-of-its-kind **Dual Hybrid Indexing** pipeline. Unlike standard AI apps that just query text documents, we marry time-series chronological databases with custom semantic memory graphs using **Cognee**. This lets us build two main features: **The Oracle**—which acts as a conversational gateway to your own past, allowing you to ask conceptual questions—and **Blindspots**, which proactively finds contradictions and hidden behavioral trends in the background."

**[Transition to Slide 5: System Architecture]**
*   **Script:** "Under the hood, we designed this as a highly secure, offline-first system. It runs locally on your device using SQLite and LanceDB to ensure your private thoughts stay private, but can seamlessly scale to Cognee Cloud for cross-device synchronization. Let’s jump directly into the live product and show you how it works."

---

### ⏱️ 01:30 - 02:45 | Demo Part 1: Slate Ingestion & Oracle Q&A
**[Switch screen to the Live Web Application on 'The Slate' tab]**
*   **Script:** "This is the Slate, our journal interface. I'm going to type a quick thought: *'Feeling immense placement interview pressure today, but played a quick match of rugby yesterday to clear my mind.'* On submit, our system goes to work. In the background, Cognee parses this text, extracts the concepts of 'placement pressure' and 'rugby', and connects them directly into my personal memory graph."

**[Switch to 'The Oracle' tab. Prepare to type a semantic query]**
*   **Script:** "Now, let's talk to our past. Let's switch to the Oracle. We've seeded 3.5 years of daily entries here. Instead of scrolling through years of diaries to find a pattern, I can simply ask: *'What happens to my coding performance when I do morning meditation?'*"

**[Type query and press Enter]**
*   **Script:** "The Oracle traverses our memory graph to find the exact historical correlations. It returns a clear, synthesized answer: morning meditation consistently puts me in a flow state, helping me solve complex algorithms effortlessly. We bypassed slow graph-traversal bottlenecks to make these conversational retrievals feel instant and seamless."

**[Ask a second prompt: 'How does staying up playing Valorant affect me?']**
*   **Script:** "We can also discover negative routines. Let's ask: *'How does staying up playing Valorant affect me?'* Instantly, it flags the pattern: late-night gaming leads to missed morning classes a day or two later. By clicking Thumbs Up, we reinforce the semantic weights of these graph nodes, ensuring our memory brain learns and updates as we grow."

---

### ⏱️ 02:45 - 03:45 | Demo Part 2: Impact & Memory Sanctuary
**[Switch to 'Blindspots' tab]**
*   **Script:** "The real **Impact** of Déjà lies in proactive wellness. Our **Blindspots Engine** compares the chronological dates in our timeline against the density of our memory graph. It acts like a proactive companion, raising **Paradox Alerts** when habits slip away. For example, it warns us: *'You used to log a lot about watching high-concept movies and playing football, but you haven't mentioned them recently.'* By flagging these abandoned routines, we help users prevent cognitive overload before it becomes a mental health crisis."

**[Switch to 'Safeguard/Sanctuary' settings, locate a memory concept like 'rugby' or 'Valorant']**
*   **Script:** "And because this is an intimate extension of your mind, privacy and control are absolute. If there is a memory or a habit you want to let go of, you can click **Dissolve**. This doesn't just delete a database row; it invokes `cognee.forget()` to prune the vector space and sever the semantic connections. The system literally loses the capacity to reason about that topic, giving you a true, conceptual 'right to be forgotten' inside your AI sanctuary."

---

### ⏱️ 03:45 - 04:15 | Slide 7: Feasibility & Business Sustainability
**[Switch screen back to Slide 7: Revenue Streams]**
*   **Script:** "To make Déjà **Feasible and Sustainable**, we designed it to be Free-First and local. Because the free tier runs entirely on local databases on the user's own device, we have **exactly $0 database hosting cost** for our core users, making the product highly scalable. For those who want cross-device sync and proactive alerts, our Pro tier uses Cognee Cloud. This consumer model is backed by our B2B strategy, where we license our platform to corporate Employee Assistance Programs (EAPs) who sponsor seats for employee mental wellness."

---

### ⏱️ 04:15 - 05:00 | Conclusion & Q&A Transition
**[Transition to Slide 13: Thank You]**
*   **Script:** "By mapping the chaos of daily thoughts into structured semantic knowledge, Déjà directly aligns with SDG 3 to prevent cognitive burnout and improve mental well-being. We are now open for your questions. Thank you!"

---

## 🎯 Step-by-Step Live Demo Execution

To ensure your demo runs smoothly without lag, follow these exact steps:

1.  **Preparation (Before the Presentation):**
    *   Open your browser and log into the React front-end.
    *   Make sure the backend servers are running (`./start.sh` should be active and the Express Gateway is up).
    *   Test one query in the **Oracle** tab beforehand to ensure the LLM cache and embedding engine are warmed up.
2.  **Step 1: Ingestion on 'The Slate'**
    *   Type: *"I've been feeling immense pressure about my placement interviews lately, but I really loved playing rugby yesterday to blow off steam."*
    *   Press Submit. Note: explain that this executes asynchronously so they don't wait for the graph compile to complete.
3.  **Step 2: Q&A on 'The Oracle'**
    *   Ask: *"What happens to my coding performance when I do morning meditation?"* (This fetches the positive pattern).
    *   Ask: *"How does eating heavy fast food for lunch affect me?"* or *"How does playing Valorant late at night affect me?"* (This fetches the negative pattern).
    *   Click the **Thumbs Up** icon to demonstrate user-guided reinforcement.
4.  **Step 3: Gaps on 'Blindspots'**
    *   Click on **Blindspots**. Show the generated alerts. Explain that these are conceptually computed using cosine similarities.
5.  **Step 4: Dissolve on 'Safeguard'**
    *   Go to settings/safeguard and click **Dissolve** on the rugby or Valorant memory. Show that it triggers the forget pipeline.

---

## ❓ Q&A Prep: Technical Explanations for Non-Technical Presenters

Judges love to test the technical feasibility of AI architectures. Here is how to answer their questions using simple but highly professional terminology:

### Q1: "How does the Blindspots Engine actually detect a contradiction or a gap?"
*   **Your Answer:** "It uses a hybrid graph-relational approach. We fetch the raw chronological log entries from Supabase to track when specific topics were last mentioned. Concurrently, we extract the semantic vector representations of these topics from our Cognee-backed LanceDB. If a topic has high conceptual weight in the vector graph (meaning it’s historically important to the user) but is completely missing from the recent chronological database timeline, our algorithm flags it as an abandoned habit or cognitive gap."

### Q2: "You mentioned reducing retrieval time from 10 seconds to 1.5 seconds. How did you optimize this?"
*   **Your Answer:** "By default, querying a semantic knowledge graph requires traversing node relationships using a slow Large Language Model (LLM) loop. To optimize this, we bypassed Cognee's internal LLM-based query executor. Instead, we use `cognee.recall()` directly to retrieve the raw subgraph context window (`top_k=150`) based on vector proximity, and then pass that raw structured data to a lightweight, local, low-latency LLM analyzer to summarize the result. This drops the round-trip API time from ~10s down to ~1.5s."

### Q3: "SQLite is notorious for database locks under concurrent write loads. How does your bridge handle multiple users?"
*   **Your Answer:** "That is a critical production issue. If multiple users attempt to run ingestion or graph compilations simultaneously, SQLite throws database lock errors. To solve this, we implemented a serialized, queue-based executor inside our Python FastAPI bridge. All incoming write requests are placed in an asynchronous queue, ensuring they are executed sequentially, one write at a time. This guarantees data integrity without crashing the local database."

### Q4: "What is the difference between your local mode and cloud mode?"
*   **Your Answer:** "Local mode runs offline, saving graph metadata in a local SQLite file and vector coordinates in LanceDB directly on the user's host. When cloud parameters are configured, the bridge promotes the connection via `cognee.serve()` to a secure Cognee Cloud hosted platform, syncing graph nodes across multiple device sessions."

### Q5: "How does Thumbs Up/Down feedback reinforce graph weights?"
*   **Your Answer:** "When a user gives feedback on a retrieved correlation, our gateway sends a weight update to the FastAPI backend. We adjust the connection weights between the query node and the retrieved memory nodes in the semantic graph. Helpful connections get stronger weights, making them more likely to be recalled in future queries."

---

## 📖 Simplified Deep-Dive: How Déjà Works under the Hood

Use these simple analogies to build an intuitive, clear understanding of how the tech works so you can answer any unexpected questions from the judges.

### 1. The Core Architecture: Why do we use both Supabase and Cognee?
*   **The Problem:** Your brain has two ways of remembering:
    1.  **The Calendar (Time):** Remembering exactly *when* you did something (e.g., *"I played rugby on Monday"*).
    2.  **The Association Web (Meaning):** Linking ideas together regardless of time (e.g., *"Rugby helps me relieve interview stress"*).
*   **How we solve it:** We marry both. **Supabase** is our chronological database (our calendar). **Cognee** is our semantic knowledge graph (our web of associations). By combining them, Déjà doesn't just search your entries like a folder of files; it understands how your experiences connect.

### 2. Ingestion (The Slate): What happens when you submit a journal entry?
*   **The Ingestion Pipeline:**
    1.  The text you type goes to our Node.js gateway and is immediately saved in a chronological timeline table inside **Supabase**.
    2.  Concurrently, the text is routed to our Python FastAPI service running **Cognee**.
    3.  Cognee reads the sentence and extracts key **entities** (nouns/concepts like *rugby*, *interview*, *burnout*) and **relationships** (actions/links like *relieves*, *triggers*).
    4.  It saves these concepts as points (nodes) and lines (edges) inside a local database (**SQLite** for graph structure and **LanceDB** for vector embeddings).

### 3. The Oracle (Conversational Q&A): How does it search your past?
*   **The Oracle Pipeline:**
    1.  When you ask, *"What affects my coding performance?"*, the Oracle doesn't do a simple keyword match (which would miss entries that don't say the exact word "performance").
    2.  It converts your question into a mathematical vector coordinates query and looks at the **LanceDB** vector database.
    3.  It finds the node representing *"coding performance"* and follows the graph paths to see what other nodes are connected to it (like *morning meditation* or *heavy lunch*).
    4.  It retrieves these connected concepts and feeds them to our local Large Language Model (LLM) wrapper, which summarizes them into a conversational answer for you.

### 4. The Blindspots Engine: How does it find your forgotten habits?
*   **The Blindspots Algorithm:**
    1.  The engine runs a scheduled matching script. It asks **Cognee**: *"What are the concepts in this user's graph that have the highest connection density?"* (e.g., *guitar*, *running*, *reading*).
    2.  Then it looks at **Supabase** and asks: *"When was the last time the user wrote about 'guitar' or 'running'?"*
    3.  If a concept is highly connected in the graph (historically important to the user) but has **zero entries** in the recent timeline, the system flags a **Paradox Alert**: *"You used to care a lot about guitar, but you haven't mentioned it recently."*
    4.  It is a simple comparison between **graph density** and **chronological frequency**.

### 5. Memory Sanctuary (Safeguard / Dissolve): How does "forgetting" actually work?
*   **The Purge Pipeline:**
    1.  In a typical app, deleting an entry just deletes a row in a database, but search indexes can still retain cached traces.
    2.  In Déjà, when you click **Dissolve** on a concept (like *Valorant*), we invoke `cognee.forget()`.
    3.  This goes directly into the vector database and the semantic graph, **cutting the lines (edges) connecting to that node** and pruning its coordinates.
    4.  Because the paths to that memory are physically dissolved, the AI literally loses the ability to retrieve or reason about that concept ever again. It is a genuine conceptual delete.

