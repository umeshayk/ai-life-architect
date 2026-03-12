import { useEffect, useState } from "react";
import api from "../api/client";

const emptyProfile = {
  goals: "",
  interests: "",
  expertise: "",
  preferred_topics: ""
};

export default function Profile() {
  const [form, setForm] = useState(emptyProfile);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.get("/profile").then((response) => {
      if (response.data) {
        setForm({
          goals: response.data.goals || "",
          interests: response.data.interests || "",
          expertise: response.data.expertise || "",
          preferred_topics: response.data.preferred_topics || ""
        });
      }
    });
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    await api.put("/profile", form);
    setMessage("Profile saved.");
  };

  return (
    <div className="card">
      <h2>Profile</h2>
      <form onSubmit={handleSubmit} className="stack">
        <textarea rows="4" placeholder="Goals" value={form.goals} onChange={(event) => setForm({ ...form, goals: event.target.value })} />
        <textarea rows="4" placeholder="Interests" value={form.interests} onChange={(event) => setForm({ ...form, interests: event.target.value })} />
        <textarea rows="4" placeholder="Expertise" value={form.expertise} onChange={(event) => setForm({ ...form, expertise: event.target.value })} />
        <textarea
          rows="4"
          placeholder="Preferred topics"
          value={form.preferred_topics}
          onChange={(event) => setForm({ ...form, preferred_topics: event.target.value })}
        />
        <button type="submit">Save Profile</button>
      </form>
      {message && <p className="success-text">{message}</p>}
    </div>
  );
}
