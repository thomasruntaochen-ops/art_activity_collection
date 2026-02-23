"use client";

import { useEffect, useMemo, useState } from "react";
import { ActivityTable } from "../components/activity-table";
import { fetchActivities, fetchSuggestions } from "../lib/api";
import { Activity } from "../lib/types";

const US_STATES = [
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
  "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT",
  "VA", "WA", "WV", "WI", "WY",
];

export default function HomePage() {
  const [age, setAge] = useState<string>("");
  const [dropIn, setDropIn] = useState<string>("");
  const [venue, setVenue] = useState<string>("");
  const [city, setCity] = useState<string>("");
  const [state, setState] = useState<string>("");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [activities, setActivities] = useState<Activity[]>([]);
  const [venueSuggestions, setVenueSuggestions] = useState<string[]>([]);
  const [citySuggestions, setCitySuggestions] = useState<string[]>([]);

  const summary = useMemo(() => `Showing ${activities.length} activity rows`, [activities.length]);

  useEffect(() => {
    const normalized = venue.trim();
    if (!normalized) {
      setVenueSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const suggestions = await fetchSuggestions("venue", normalized);
        setVenueSuggestions(suggestions);
      } catch {
        setVenueSuggestions([]);
      }
    }, 180);
    return () => clearTimeout(timer);
  }, [venue]);

  useEffect(() => {
    const normalized = city.trim();
    if (!normalized) {
      setCitySuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const suggestions = await fetchSuggestions("city", normalized);
        setCitySuggestions(suggestions);
      } catch {
        setCitySuggestions([]);
      }
    }, 180);
    return () => clearTimeout(timer);
  }, [city]);

  async function onSearch() {
    setLoading(true);
    setError("");
    try {
      const rows = await fetchActivities({
        age: age ? Number(age) : undefined,
        drop_in: dropIn === "" ? undefined : dropIn === "true",
        venue: venue || undefined,
        city: city || undefined,
        state: state || undefined,
        date_from: dateFrom ? new Date(`${dateFrom}T00:00:00`).toISOString() : undefined,
        date_to: dateTo ? new Date(`${dateTo}T23:59:59`).toISOString() : undefined,
      });
      setActivities(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <header>
        <h1>Art Activity Collection</h1>
        <p>Free kids/teen art activities</p>
      </header>

      <section className="filters">
        <label>
          Age
          <input
            type="number"
            min={0}
            max={120}
            value={age}
            onChange={(e) => setAge(e.target.value)}
          />
        </label>

        <label>
          Drop-in
          <select value={dropIn} onChange={(e) => setDropIn(e.target.value)}>
            <option value="">Any</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        </label>

        <label>
          Venue
          <input
            type="text"
            value={venue}
            onChange={(e) => setVenue(e.target.value)}
            list="venue-suggestions"
          />
          <datalist id="venue-suggestions">
            {venueSuggestions.map((item) => (
              <option key={item} value={item} />
            ))}
          </datalist>
        </label>

        <label>
          City
          <input
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            list="city-suggestions"
          />
          <datalist id="city-suggestions">
            {citySuggestions.map((item) => (
              <option key={item} value={item} />
            ))}
          </datalist>
        </label>

        <label>
          State
          <select value={state} onChange={(e) => setState(e.target.value)}>
            <option value="">Any</option>
            {US_STATES.map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
        </label>

        <label>
          Date From
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </label>

        <label>
          Date To
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </label>

        <button onClick={onSearch} disabled={loading}>
          {loading ? "Loading..." : "Search"}
        </button>
      </section>

      <section className="summary">
        <span>{summary}</span>
        {error ? <span className="error">Error: {error}</span> : null}
      </section>

      <ActivityTable activities={activities} />
    </main>
  );
}
