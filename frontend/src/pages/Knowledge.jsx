import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import api from "../api/client";

const initialForm = { type: "note", title: "", content: "", source_url: "" };
const formatTypeLabel = (type) => type.charAt(0).toUpperCase() + type.slice(1);
const STARTER_KITS = {
  "hybrid search": [
    "What is Hybrid Search?",
    "BM25 vs Vector Search",
    "Why combine keyword and semantic search?",
    "Hybrid Search architecture example",
    "When should Hybrid Search be used?"
  ],
  "vector databases": [
    "What is a Vector Database?",
    "Why pgvector vs Pinecone?",
    "Similarity search basics",
    "Index types in vector search"
  ],
  "spawn quality": [
    "What is spawn quality in mushroom farming?",
    "How poor spawn affects yield",
    "How to identify healthy spawn",
    "Best practices for mushroom spawn handling"
  ],
  "nikhilam sutra": [
    "What is Nikhilam Sutra?",
    "Subtraction from base numbers",
    "Multiplication near powers of 10",
    "Worked examples of Nikhilam"
  ]
};

function getStarterPrompts(topic) {
  const normalizedTopic = topic.trim().toLowerCase();
  return (
    STARTER_KITS[normalizedTopic] || [
      `What is ${topic}?`,
      `Why is ${topic} important?`,
      `Core concepts of ${topic}`,
      `Beginner examples of ${topic}`,
      `Common mistakes in ${topic}`
    ]
  );
}

function buildStarterDraft(topic, prompt) {
  return {
    title: `${topic} - ${prompt}`,
    content: `Topic: ${topic}

Question:
${prompt}

Notes:

Definition:

Key Concepts:

Example:

Why it matters:

Related topics:
`
  };
}

export default function Knowledge() {
  const [searchParams, setSearchParams] = useSearchParams();
  const formRef = useRef(null);
  const contentRef = useRef(null);
  const [items, setItems] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [relatedItems, setRelatedItems] = useState({});
  const [expandedId, setExpandedId] = useState(null);
  const [loadingRelatedId, setLoadingRelatedId] = useState(null);
  const [query, setQuery] = useState("");
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [searchError, setSearchError] = useState("");
  const [searching, setSearching] = useState(false);
  const topicFilter = searchParams.get("topic")?.trim() || "";

  const loadItems = async () => {
    const response = await api.get("/knowledge");
    setItems(response.data);
  };

  useEffect(() => {
    loadItems();
  }, []);

  useEffect(() => {
    if (!topicFilter) {
      return;
    }

    setForm((current) => {
      if (current.title.trim()) {
        return current;
      }
      return { ...current, title: topicFilter };
    });
  }, [topicFilter]);

  const handleCreate = async (event) => {
    event.preventDefault();
    setError("");
    try {
      await api.post("/knowledge", {
        ...form,
        source_url: form.source_url.trim() || null
      });
      setForm(initialForm);
      await loadItems();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to save knowledge item.");
    }
  };

  const handleDelete = async (id) => {
    await api.delete(`/knowledge/${id}`);
    await loadItems();
  };

  const toggleRelated = async (id) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    if (relatedItems[id]) {
      return;
    }
    setLoadingRelatedId(id);
    try {
      const response = await api.get(`/api/connections/${id}`);
      setRelatedItems((current) => ({ ...current, [id]: response.data.related_items }));
    } finally {
      setLoadingRelatedId(null);
    }
  };

  const handleSearch = async (event) => {
    event.preventDefault();
    setSearchError("");
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const response = await api.post("/api/ai/search", { query, top_k: 5 });
      setSearchResults(response.data);
    } catch (err) {
      setSearchError(err.response?.data?.detail || "Semantic search failed.");
    } finally {
      setSearching(false);
    }
  };

  const clearSearch = () => {
    setQuery("");
    setSearchResults([]);
    setSearchError("");
    if (topicFilter) {
      const nextParams = new URLSearchParams(searchParams);
      nextParams.delete("topic");
      setSearchParams(nextParams, { replace: true });
    }
  };

  const displayedItems = useMemo(() => {
    if (query.trim()) {
      return searchResults;
    }
    if (topicFilter) {
      return items.filter((item) =>
        Array.isArray(item.topics) &&
        item.topics.some((topic) => topic.name.toLowerCase() === topicFilter.toLowerCase())
      );
    }
    return items;
  }, [items, query, searchResults, topicFilter]);

  const hasEmptyTopicState = Boolean(topicFilter) && !query.trim() && displayedItems.length === 0;
  const starterPrompts = useMemo(() => (topicFilter ? getStarterPrompts(topicFilter) : []), [topicFilter]);

  useEffect(() => {
    if (!hasEmptyTopicState || !formRef.current) {
      return;
    }

    formRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [hasEmptyTopicState]);

  const handleStarterPrompt = (prompt) => {
    const draft = buildStarterDraft(topicFilter, prompt);
    setForm({
      type: "note",
      title: draft.title,
      content: draft.content,
      source_url: ""
    });
    formRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    window.setTimeout(() => {
      contentRef.current?.focus();
      contentRef.current?.setSelectionRange(contentRef.current.value.length, contentRef.current.value.length);
    }, 250);
  };

  return (
    <div className="page-grid">
      <section ref={formRef} className={`card ${hasEmptyTopicState ? "topic-form-highlight" : ""}`}>
        <h2>Save Knowledge</h2>
        {hasEmptyTopicState && (
          <p className="success-text">
            You haven&apos;t saved knowledge about {topicFilter} yet. Add your first note below to start learning this
            topic.
          </p>
        )}
        <form onSubmit={handleCreate} className="stack">
          <select value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value })}>
            <option value="note">Note</option>
            <option value="link">Link</option>
          </select>
          <input
            placeholder="Title"
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
          />
          <textarea
            ref={contentRef}
            placeholder="Content"
            rows="8"
            value={form.content}
            onChange={(event) => setForm({ ...form, content: event.target.value })}
          />
          {form.type === "link" && (
            <input
              placeholder="Source URL"
              value={form.source_url}
              onChange={(event) => setForm({ ...form, source_url: event.target.value })}
            />
          )}
          {error && <p className="error-text">{error}</p>}
          <button type="submit">Save Item</button>
        </form>
      </section>

      <section className="stack">
        <div className="card">
          <h2>Semantic Search</h2>
          <form onSubmit={handleSearch} className="inline-form">
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search your knowledge" />
            <button type="submit">{searching ? "Searching..." : "Search"}</button>
            {query.trim() && (
              <button type="button" className="secondary-button" onClick={clearSearch}>
                Clear
              </button>
            )}
          </form>
          {searchError && <p className="error-text">{searchError}</p>}
          {query.trim() && searchResults.length === 0 && !searching && !searchError && (
            <p className="muted">No sources found.</p>
          )}
        </div>

        <div className="card">
          <div className="row-between">
            <h2>{query.trim() ? "Semantic Results" : topicFilter ? `Saved Items for ${topicFilter}` : "Saved Items"}</h2>
            {topicFilter && !query.trim() && (
              <button type="button" className="secondary-button" onClick={clearSearch}>
                Clear Topic Filter
              </button>
            )}
          </div>
          <div className="stack compact">
            {!displayedItems.length && topicFilter && !query.trim() && (
              <>
                <p className="muted">
                  You haven&apos;t saved knowledge about {topicFilter} yet. Add your first note below to start learning
                  this topic.
                </p>
                <div className="starter-kit-card">
                  <h3>Starter Kit for {topicFilter}</h3>
                  <p className="muted">Choose one to create your first learning note.</p>
                  <div className="tag-list">
                    {starterPrompts.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        className="starter-chip"
                        onClick={() => handleStarterPrompt(prompt)}
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}
            {displayedItems.map((item) => (
              <article key={item.id} className="result-item">
                <div className="row-between">
                  <div>
                    <strong>{item.title}</strong>
                    <p className="muted">
                      {formatTypeLabel(item.type)}
                      {typeof item.similarity === "number" ? ` | ${Math.round(item.similarity * 100)}% match` : ""}
                    </p>
                  </div>
                  <div className="action-row">
                    <button type="button" className="secondary-button" onClick={() => toggleRelated(item.id)}>
                      {expandedId === item.id ? "Hide Related" : "Show Related"} ({relatedItems[item.id]?.length ?? item.related_count ?? 0})
                    </button>
                    {typeof item.similarity !== "number" && (
                      <button type="button" className="danger-button" onClick={() => handleDelete(item.id)}>
                        Delete
                      </button>
                    )}
                  </div>
                </div>
                <p>{item.summary || "No summary available."}</p>
                {Array.isArray(item.tags) && (
                  <div className="tag-list">
                    {item.tags.map((tag) => (
                      <span key={`${item.id}-${tag}`} className="tag">{tag}</span>
                    ))}
                  </div>
                )}
                {Array.isArray(item.topics) && item.topics.length > 0 && (
                  <div className="tag-list">
                    {item.topics.map((topic) => (
                      <span key={`${item.id}-topic-${topic.id}`} className="tag">
                        {topic.name}
                      </span>
                    ))}
                  </div>
                )}
                {expandedId === item.id && (
                  <div className="related-block">
                    <h4>Related Knowledge</h4>
                    {loadingRelatedId === item.id ? (
                      <p className="muted">Loading related items...</p>
                    ) : (relatedItems[item.id] || []).length > 0 ? (
                      <div className="stack compact">
                        {relatedItems[item.id].map((related) => (
                          <article key={`${item.id}-${related.id}`} className="related-item">
                            <strong>{related.title}</strong>
                            <p className="muted">
                              {formatTypeLabel(related.type)} | {Math.round(related.similarity_score * 100)}% match
                            </p>
                            <p>{related.summary || "No summary available."}</p>
                          </article>
                        ))}
                      </div>
                    ) : (
                      <p className="muted">No related knowledge found yet.</p>
                    )}
                  </div>
                )}
              </article>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
