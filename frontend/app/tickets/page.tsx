"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createTicket, fetchMe, fetchTickets } from "@/lib/api";
import { Ticket, User } from "@/lib/types";

const PRIORITIES = ["P1", "P2", "P3", "P4", "P5"];

const STATUS_STYLE: Record<string, string> = {
  open: "bg-amber-50 text-amber-700 border-amber-200",
  closed: "bg-slate-100 text-slate-500 border-slate-200",
};

export default function TicketsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(true);

  const [category, setCategory] = useState("");
  const [subcategory, setSubcategory] = useState("");
  const [priority, setPriority] = useState("P3");
  const [summary, setSummary] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMe()
      .then(({ user }) => setUser(user))
      .catch(() => router.push("/login"))
      .finally(() => setCheckingAuth(false));
  }, [router]);

  useEffect(() => {
    if (!user) return;
    refreshTickets();
  }, [user]);

  async function refreshTickets() {
    setLoadingTickets(true);
    try {
      const data = await fetchTickets();
      setTickets(data);
    } catch {
      // Non-fatal: list just won't update this time.
    } finally {
      setLoadingTickets(false);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      await createTicket({ category, subcategory, priority, summary });
      setCategory("");
      setSubcategory("");
      setPriority("P3");
      setSummary("");
      await refreshTickets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the ticket.");
    } finally {
      setSubmitting(false);
    }
  }

  if (checkingAuth) {
    return (
      <main className="flex h-screen items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-400">Loading…</p>
      </main>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-slate-900">Tickets</h1>
            <p className="text-xs text-slate-500">
              Raise a ticket yourself if the assistant couldn&apos;t resolve your issue.
            </p>
          </div>
          <Link
            href="/"
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            &larr; Back to chat
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-8">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900">Raise a new ticket</h2>

          <form onSubmit={handleSubmit} className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-slate-600">
                Category
              </label>
              <input
                required
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g. Hardware"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600">
                Subcategory
              </label>
              <input
                value={subcategory}
                onChange={(e) => setSubcategory(e.target.value)}
                placeholder="e.g. Laptop"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
              >
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-slate-600">
                Describe the issue
              </label>
              <textarea
                required
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                rows={3}
                placeholder="What's going on?"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
              />
            </div>

            {error && (
              <p className="sm:col-span-2 text-sm text-red-600">{error}</p>
            )}

            <div className="sm:col-span-2">
              <button
                type="submit"
                disabled={submitting}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {submitting ? "Raising ticket…" : "Raise ticket"}
              </button>
            </div>
          </form>
        </section>

        <section className="mt-8">
          <h2 className="text-sm font-semibold text-slate-900">Your tickets</h2>

          {loadingTickets ? (
            <p className="mt-4 text-sm text-slate-400">Loading…</p>
          ) : tickets.length === 0 ? (
            <p className="mt-4 text-sm text-slate-400">
              No tickets yet. Raised tickets — yours or the assistant&apos;s — will show up here.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {tickets.map((ticket) => (
                <li
                  key={ticket.id}
                  className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-mono text-sm text-slate-900">
                      {ticket.ticket_number}
                    </span>
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded-full border px-2 py-0.5 text-xs font-medium ${
                          STATUS_STYLE[ticket.status] ?? STATUS_STYLE.open
                        }`}
                      >
                        {ticket.status}
                      </span>
                      <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs text-slate-500">
                        {ticket.priority}
                      </span>
                      <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs text-slate-500">
                        {ticket.source === "agent" ? "Raised by assistant" : "Raised by you"}
                      </span>
                    </div>
                  </div>

                  <p className="mt-2 text-sm text-slate-700">
                    {ticket.category}
                    {ticket.subcategory ? ` — ${ticket.subcategory}` : ""}
                  </p>
                  <p className="mt-1 text-sm text-slate-500">{ticket.summary}</p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
