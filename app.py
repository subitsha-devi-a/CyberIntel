
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

from modules.rag_engine import retrieve_context
from modules.graphrag_engine import build_hybrid_context

from modules.persistent_cag import (
    get_answer,
    save_answer,
    memory_count,
    clear_memory
)

from modules.document_ingestion import (
    extract_pdf_text,
    add_document
)

from knowledge_graph.graph_engine import (
    build_knowledge_graph,
    get_graph_relationships
)

from nexus_client import ask_nexus, test_nexus_connection


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="CyberIntel",
    page_icon="🛡️",
    layout="wide"
)


# ==================================================
# RESPONSE VALIDATION
# ==================================================

def is_blocked_or_failed(answer):

    text = str(answer).lower()

    error_messages = [
        "blocked by our content filters",
        "nexus content filter response",
        "nexus refusal",
        "content_filter",
        "nexus api returned",
        "nexus api request failed",
        "nexus api configuration",
        "nexus api request timed out",
        "unexpected nexus api",
        "no response choices",
        "nexus returned an empty answer",
        "nexus could not generate an answer",
        "nexus blocked the response",
        "question-only attempt",
        "context-based attempt"
    ]

    return any(message in text for message in error_messages)


def is_general_knowledge_retry(answer):

    return str(answer).startswith(
        "NEXUS GENERAL-KNOWLEDGE RETRY"
    )


# ==================================================
# PREPARE RETRIEVED CONTEXT
# ==================================================

def prepare_safe_context(evidence):

    if not evidence:
        return "No supporting records were retrieved."

    records = []

    for index, item in enumerate(evidence[:4], start=1):

        title = str(item.get("title", "Unknown"))[:150]
        category = str(item.get("category", "Unknown"))[:100]
        source = str(item.get("source", "Not available"))[:250]

        method = str(
            item.get("retrieval_method", "Hybrid retrieval")
        )[:100]

        records.append(
            f"Reference {index}\n"
            f"Title: {title}\n"
            f"Category: {category}\n"
            f"Source: {source}\n"
            f"Retrieval method: {method}"
        )

    return (
        "The following are reference metadata records retrieved "
        "from the CyberIntel knowledge base. Use them as pointers "
        "to relevant sources. Do not treat metadata as proof of "
        "technical details.\n\n"
        + "\n\n".join(records)
    )


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

st.sidebar.title("CyberIntel Navigation")

page = st.sidebar.radio(
    "Select Module",
    [
        "Dashboard",
        "Threat Intelligence",
        "Document Upload",
        "AI Threat Analysis",
        "GraphRAG Explorer",
        "Knowledge Graph",
        "CAG Memory"
    ]
)


# ==================================================
# APPLICATION HEADER
# ==================================================

st.title("CyberIntel")

st.subheader(
    "AI-Powered Cyber Threat Intelligence and Attack Relationship Discovery"
)

st.caption(
    "Hybrid GraphRAG | Vector RAG | CAG | Knowledge Graph | Nexus AI"
)


# ==================================================
# 1. DASHBOARD
# ==================================================

if page == "Dashboard":

    st.header("Cybersecurity Dashboard")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("RAG Engine", "Active")
    c2.metric("GraphRAG", "Active")
    c3.metric("CAG Memories", memory_count())
    c4.metric("Knowledge Graph", "Active")

    st.info(
        "CyberIntel combines document retrieval, semantic search, "
        "graph-based relationship discovery and AI analysis."
    )

    st.subheader("Nexus API Connection")

    if st.button("Test Nexus API Connection"):

        with st.spinner("Testing Nexus API connection..."):

            result = test_nexus_connection()

        if result.get("success"):

            st.success(
                result.get("message", "Connection successful.")
            )

        else:

            st.error(
                result.get("message", "Connection failed.")
            )


# ==================================================
# 2. THREAT INTELLIGENCE
# ==================================================

elif page == "Threat Intelligence":

    st.header("Threat Intelligence Search")

    question = st.text_input(
        "Search cybersecurity information"
    )

    if st.button("Search Threat"):

        if not question.strip():

            st.warning("Please enter a search query.")

        else:

            with st.spinner("Searching threat knowledge base..."):

                try:

                    results = retrieve_context(question)

                    if results:

                        for item in results:

                            st.subheader(
                                item.get("title", "Unknown")
                            )

                            st.write(
                                item.get("content", "")
                            )

                            st.caption(
                                "Category: "
                                + str(item.get("category", "Unknown"))
                            )

                            source = item.get("source", "")

                            if source.startswith(
                                ("http://", "https://")
                            ):

                                st.markdown(
                                    f"[View Source]({source})"
                                )

                            st.divider()

                    else:

                        st.warning(
                            "No matching threat records found."
                        )

                except Exception as error:

                    st.error(
                        f"Threat search failed: {error}"
                    )


# ==================================================
# 3. DOCUMENT UPLOAD
# ==================================================

elif page == "Document Upload":

    st.header("Cybersecurity Document Upload")

    uploaded_file = st.file_uploader(
        "Upload a cybersecurity PDF",
        type=["pdf"]
    )

    if uploaded_file is not None:

        st.write(
            "Selected file:",
            uploaded_file.name
        )

        if st.button("Extract and Add to Knowledge Base"):

            try:

                with st.spinner("Extracting PDF content..."):

                    content = extract_pdf_text(uploaded_file)

                if content and content.strip():

                    success = add_document(
                        uploaded_file.name,
                        content
                    )

                    if success:

                        st.success(
                            "PDF content added to the knowledge base!"
                        )

                        st.write(
                            "Extracted characters:",
                            len(content)
                        )

                    else:

                        st.error(
                            "Could not add the document to the knowledge base."
                        )

                else:

                    st.warning(
                        "No readable text found in this PDF."
                    )

            except Exception as error:

                st.error(
                    f"PDF processing failed: {error}"
                )


# ==================================================
# 4. AI THREAT ANALYSIS
# ==================================================

elif page == "AI Threat Analysis":

    st.header("AI-Powered Threat Analysis")

    question = st.text_area(
        "Enter your cybersecurity question",
        placeholder="Example: Explain Log4Shell vulnerability and its possible impact."
    )

    if st.button("Generate AI Analysis", type="primary"):

        if not question.strip():

            st.warning("Please enter a question.")

        else:

            # STEP 1: HYBRID RETRIEVAL

            try:

                with st.spinner("Retrieving hybrid evidence..."):

                    context, evidence = build_hybrid_context(question)

            except Exception as error:

                st.error(
                    f"Hybrid retrieval failed: {error}"
                )

                context = ""
                evidence = []

            # STEP 2: PREPARE CONTEXT

            safe_context = prepare_safe_context(evidence)

            # STEP 3: CHECK PERSISTENT CAG MEMORY

            try:

                cached = get_answer(
                    question,
                    safe_context
                )

            except Exception as error:

                cached = None

                st.warning(
                    f"CAG memory lookup failed: {error}"
                )

            # STEP 4: DISPLAY VALID CACHED ANSWER

            if cached and not is_blocked_or_failed(cached):

                st.info(
                    "Answer retrieved from persistent CAG memory."
                )

                st.subheader("Analysis Result")

                st.write(cached)

            else:

                # STEP 5: GENERATE NEXUS RESPONSE

                with st.spinner(
                    "Generating AI analysis using Nexus..."
                ):

                    answer = ask_nexus(
                        question,
                        safe_context
                    )

                # STEP 6: CHECK RESPONSE

                if is_blocked_or_failed(answer):

                    st.error(
                        "Nexus could not generate this answer. "
                        "The response was not saved in CAG memory."
                    )

                    st.code(
                        str(answer),
                        language="text"
                    )

                elif is_general_knowledge_retry(answer):

                    # QUESTION-ONLY RETRY
                    # DO NOT SAVE AS CONTEXT-GROUNDED CAG ANSWER

                    st.warning(
                        "Nexus generated this answer without retrieved "
                        "context. Retrieved evidence is displayed separately. "
                        "This answer was not saved as a context-grounded "
                        "CAG response."
                    )

                    st.subheader("General Knowledge Analysis")

                    clean_answer = str(answer).replace(
                        "NEXUS GENERAL-KNOWLEDGE RETRY",
                        "",
                        1
                    ).strip()

                    st.write(clean_answer)

                else:

                    # FULL CONTEXT-BASED NEXUS ANSWER

                    try:

                        save_answer(
                            question,
                            safe_context,
                            answer
                        )

                        st.success(
                            "Fresh Nexus AI analysis generated and saved in CAG memory."
                        )

                    except Exception as error:

                        st.warning(
                            f"Answer generated, but CAG saving failed: {error}"
                        )

                    st.subheader("Analysis Result")

                    st.write(answer)

            # STEP 7: DISPLAY RETRIEVED EVIDENCE

            st.divider()

            st.subheader("Retrieved Evidence")

            if evidence:

                for item in evidence:

                    st.write(
                        "**"
                        + str(item.get("title", "Unknown"))
                        + "**"
                    )

                    st.caption(
                        "Category: "
                        + str(item.get("category", "Unknown"))
                    )

                    st.caption(
                        "Retrieval method: "
                        + str(
                            item.get(
                                "retrieval_method",
                                "Unknown"
                            )
                        )
                    )

            else:

                st.warning(
                    "No supporting evidence was retrieved."
                )


# ==================================================
# 5. HYBRID GRAPHRAG EXPLORER
# ==================================================

elif page == "GraphRAG Explorer":

    st.header("Hybrid GraphRAG Explorer")

    question = st.text_input(
        "Enter a cybersecurity query"
    )

    if st.button("Discover Relationships"):

        if not question.strip():

            st.warning("Enter a query.")

        else:

            try:

                with st.spinner(
                    "Running Hybrid GraphRAG retrieval..."
                ):

                    context, results = build_hybrid_context(question)

                if results:

                    for item in results:

                        st.subheader(
                            item.get("title", "Unknown")
                        )

                        st.caption(
                            "Retrieved using: "
                            + str(
                                item.get(
                                    "retrieval_method",
                                    "Unknown"
                                )
                            )
                        )

                        st.write(
                            item.get("content", "")
                        )

                        st.divider()

                else:

                    st.warning(
                        "No related information found."
                    )

            except Exception as error:

                st.error(
                    f"GraphRAG retrieval failed: {error}"
                )


# ==================================================
# 6. KNOWLEDGE GRAPH
# ==================================================

elif page == "Knowledge Graph":

    st.header("Cyber Attack Relationship Graph")

    try:

        graph = build_knowledge_graph()

        if graph.number_of_nodes() == 0:

            st.warning("Knowledge graph is empty.")

        else:

            network = Network(
                height="550px",
                width="100%",
                directed=True,
                bgcolor="#111827",
                font_color="white"
            )

            for node, details in graph.nodes(data=True):

                network.add_node(
                    node,
                    label=details.get("label", str(node)),
                    title=details.get("description", "")
                )

            for source, target, details in graph.edges(data=True):

                network.add_edge(
                    source,
                    target,
                    label=details.get("relation", "RELATED_TO")
                )

            components.html(
                network.generate_html(),
                height=570,
                scrolling=True
            )

            st.subheader("Detected Relationships")

            relationships = get_graph_relationships()

            if relationships:

                for relation in relationships:

                    st.write(
                        str(relation.get("source", "Unknown"))
                        + " → "
                        + str(
                            relation.get(
                                "relationship",
                                "RELATED_TO"
                            )
                        )
                        + " → "
                        + str(relation.get("target", "Unknown"))
                    )

            else:

                st.info("No relationships detected.")

    except Exception as error:

        st.error(
            f"Knowledge graph loading failed: {error}"
        )


# ==================================================
# 7. PERSISTENT CAG MEMORY
# ==================================================

elif page == "CAG Memory":

    st.header("Persistent Context-Augmented Generation Memory")

    st.metric(
        "Stored Analysis Contexts",
        memory_count()
    )

    st.write(
        "Successfully generated context-based analysis answers "
        "and their retrieved reference contexts are stored in SQLite."
    )

    st.caption(
        "Question-only Nexus retries are not saved as context-grounded answers."
    )

    if st.button("Clear CAG Memory"):

        try:

            clear_memory()

            st.success("CAG memory cleared.")

            st.rerun()

        except Exception as error:

            st.error(
                f"Could not clear CAG memory: {error}"
            )


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "CyberIntel | Hybrid GraphRAG and CAG | Academic Final-Year Project"
)
