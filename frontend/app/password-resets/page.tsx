"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createPasswordReset, fetchMe, fetchPasswordResets } from "@/lib/api";
import { PasswordResetRequest, User } from "@/lib/types";

const STATUS_STYLE: Record<string, string> = {
  queued: "bg-amber-50 text-amber-700 border-amber-200",
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
};

export default function PasswordResetsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [requests, setRequests] = useState<PasswordResetRequest[]>([]);
  const [loadingRequests, setLoadingRequests] = useState(true);

  const [username, setUsername] = useState("");
  const [reason, setReason] = useState("");
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
    refreshRequests();
  }, [user]);

  async function refreshRequests() {
    setLoadingRequests(true);
    try {
      const data = await fetchPasswordResets();
      setRequests(data);
    } catch {
      // Non-fatal: list just won't update this time.
    } finally {
      setLoadingRequests(false);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      await createPasswordReset({ username, reason });
      setUsername("");
      setReason("");
      await refreshRequests();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit the request.");
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
            <h1 className="text-lg font-semibold text-slate-900">Password Resets</h1>
            <p className="text-xs text-slate-500">
              Request a password reset yourself, or let the assistant queue one for you.
            </p>
          </div>
          <Link href="/" className="text-sm text-blue-600 hover:text-blue-800">
            &larr; Back to chat
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-8">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900">Request a password reset</h2>

          <form onSubmit={handleSubmit} className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-slate-600">
                Username / account
              </label>
              <input
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. jdoe"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600">
                Reason (optional)
              </label>
              <input
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g. Forgot my password"
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
                {submitting ? "Submitting…" : "Request reset"}
              </button>
            </div>
          </form>
        </section>

        <section className="mt-8">
          <h2 className="text-sm font-semibold text-slate-900">Your reset requests</h2>

          {loadingRequests ? (
            <p className="mt-4 text-sm text-slate-400">Loading…</p>
          ) : requests.length === 0 ? (
            <p className="mt-4 text-sm text-slate-400">
              No reset requests yet. Requests — yours or the assistant&apos;s — will show up here.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {requests.map((request) => (
                <li
                  key={request.id}
                  className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-mono text-sm text-slate-900">
                      {request.username}
                    </span>
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded-full border px-2 py-0.5 text-xs font-medium ${
                          STATUS_STYLE[request.status] ?? STATUS_STYLE.queued
                        }`}
                      >
                        {request.status}
                      </span>
                      <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs text-slate-500">
                        {request.source === "agent" ? "Raised by assistant" : "Raised by you"}
                      </span>
                    </div>
                  </div>

                  {request.reason && (
                    <p className="mt-2 text-sm text-slate-500">{request.reason}</p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
