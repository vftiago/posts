---
title: Frontend Architecture Interview — Crypto Price Dashboard
published: false
description: Walking through a frontend system design interview, from requirements analysis to scalable architecture.
tags: react, system-design, interview, architecture
cover_image:
---

This post walks through a frontend-focused system design interview. The format is open-ended and conversational — the kind where you're expected to drive the discussion, ask clarifying questions, and justify your decisions. I'll work through it as if explaining my reasoning to the interviewer in real time.

## The Prompt

> We're speccing out the home page for a new crypto mobile app. Users want to see the prices of the top five cryptocurrencies, updated in near real-time. Design a technical solution.

**Requirements**

- Data must update within 5 seconds maximum
- Show a "last updated" timestamp
- Show when data is fetching
- Handle errors gracefully
- Scale to approximately 5 million users

**Data Providers**

- Kraken — WebSocket only (hard requirement)
- Coinbase — REST API only (hard requirement)

**Platform**

- React Native mobile app

## First Impressions

This prompt has a trap. Because this is a frontend challenge, the instinct might be to start thinking about how we're going to build our app right away. But there's a more fundamental question:

**Can the mobile app talk directly to Kraken and Coinbase, or does something need to sit in between?**

This is the architectural fork in the road. If clients can connect directly, the React Native app handles WebSocket connections to Kraken, REST polling to Coinbase, data normalization, and failover logic. If we need a backend, the app becomes simpler — but we need to design what it talks to.

That decision shapes everything: the data fetching strategy, the state management approach, the error handling model, even the offline behavior. A frontend architect needs to reason through this layer, not because they'll implement the backend, but because the frontend's design is constrained by what sits on the other side of the network.

Let's work through it.

## The Critical Question: Do We Need a Backend?

Could clients connect directly to Kraken and Coinbase?

**Direct WebSocket to Kraken**

Kraken's WebSocket API is designed for individual traders, not for distributing data to millions of app users. If 5 million clients each open a WebSocket connection to Kraken:

- Kraken would rate-limit or ban us immediately
- We'd be abusing their infrastructure
- We'd have no control over failover, data normalization, or business logic

**Direct REST polling to Coinbase**

If 5 million clients each poll Coinbase every 5 seconds:

- That's 1 million requests per second to Coinbase
- We'd hit rate limits within seconds
- Again: banned, no control, no fallback

**Verdict: We need a backend.**

The backend's job is to aggregate data from upstream providers (as a single well-behaved client) and distribute it to our users (at whatever scale we need). This is a standard fan-out pattern.

## Designing the Backend

The backend has two responsibilities:

1. **Ingest** — Connect to Kraken and Coinbase, normalize the data
2. **Distribute** — Serve that data to millions of mobile clients

### Ingestion Layer

We need a service that:

- Maintains a persistent WebSocket connection to Kraken
- Polls Coinbase REST API every few seconds
- Normalizes responses into a common format
- Handles source failures gracefully

This can be a small, single-purpose service. It doesn't need to scale horizontally — it's just one (or a few, for redundancy) well-behaved client talking to upstream APIs.

### Why We Need Shared State

The ingestion service receives data continuously — Kraken pushes via WebSocket, we poll Coinbase on an interval. But HTTP API servers handling client requests are stateless and may run as multiple instances behind a load balancer. We need a way for the ingestion service to publish data that all API servers can read.

Options:

1. **In-memory (single server)** — The ingestion service and API server are the same process. Simple, but a single point of failure and no horizontal scaling.

2. **In-memory with pub/sub** — Ingestion service publishes to a message bus; API servers subscribe and cache locally. More complex, and each server maintains its own cache.

3. **Shared cache (Redis/Memcached)** — Ingestion service writes to a cache; API servers read from it. Simple, decoupled, and horizontally scalable.

For this use case, option 3 makes the most sense. The data is small (prices for 5 cryptocurrencies), read-heavy (millions of reads per second, one write every few seconds), and needs to be consistent across all API servers. Redis is a common choice: it's fast, widely supported, and handles this read/write pattern well. Memcached would also work — we don't need Redis's advanced features here.

```
┌─────────────────────────────────────────────────────┐
│                  Ingestion Service                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│       ┌─────────────┐         ┌─────────────┐       │
│       │   Kraken    │         │  Coinbase   │       │
│       │  WebSocket  │         │   Poller    │       │
│       │  Listener   │         │(3s interval)│       │
│       └──────┬──────┘         └──────┬──────┘       │
│              │                       │              │
│              └───────────┬───────────┘              │
│                          ▼                          │
│                 ┌─────────────────┐                 │
│                 │   Normalizer    │                 │
│                 │  & Aggregator   │                 │
│                 └────────┬────────┘                 │
│                          ▼                          │
│                 ┌─────────────────┐                 │
│                 │  Cache (Redis)  │                 │
│                 └─────────────────┘                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Data Normalization

Kraken and Coinbase return different response formats. The normalizer produces a canonical shape:

```typescript
interface PriceData {
  prices: {
    symbol: string; // "BTC", "ETH", etc.
    price: number; // USD price
    change24h: number; // percentage
    source: "kraken" | "coinbase";
  }[];
  timestamp: number; // Unix timestamp of last update
  sources: {
    kraken: { status: "connected" | "stale" | "down"; lastUpdate: number };
    coinbase: { status: "connected" | "stale" | "down"; lastUpdate: number };
  };
}
```

Including source metadata lets the frontend display appropriate warnings if one provider is degraded.

### Aggregation Strategy

We have two sources that may report slightly different prices (exchanges have different order books). Options:

1. **Primary/fallback** — Use Kraken as primary (real-time), Coinbase as fallback
2. **Average** — Show the mean of both sources
3. **Show both** — Display a range or both prices

For a consumer app, option 1 is simplest. Kraken's WebSocket gives us real-time data; Coinbase serves as a health check and fallback. If prices diverge significantly (say, more than 2%), we could flag the data as uncertain — but that's an edge case we'd refine after observing real behavior.

### Distribution Layer

Now the harder question: how do we get this data to 5 million mobile clients with sub-5-second latency?

**Option A: WebSocket from backend to clients**

Each client opens a WebSocket to our backend. When prices update, we push to all connected clients.

Challenges:

- 5 million concurrent WebSocket connections requires significant infrastructure
- WebSocket load balancing is more complex than HTTP (sticky sessions, connection state)
- Mobile clients on flaky networks mean constant reconnection churn
- Higher battery drain on mobile devices (persistent connection)

**Option B: Server-Sent Events (SSE)**

Similar to WebSocket but simpler (HTTP-based, one-way). Still requires persistent connections, so the scaling challenges remain.

**Option C: Client polling with aggressive caching**

Clients poll a REST endpoint every 3-5 seconds. The endpoint is backed by a CDN with a short TTL.

A **CDN (Content Delivery Network)** is a globally distributed network of servers that cache and serve content from locations close to users. When a user in Tokyo requests data, they hit a CDN server in Tokyo rather than our origin server in, say, Virginia. This reduces latency and offloads traffic from our infrastructure.

CDNs are typically associated with static assets (images, JavaScript bundles), but they work equally well for API responses. The key is the `Cache-Control` header: we tell the CDN how long a response is valid. For our price data, a 2-second TTL means the CDN caches each response for 2 seconds before fetching a fresh copy from our origin.

Setting up a CDN is straightforward with modern providers. Services like Cloudflare, AWS CloudFront, or Fastly sit in front of your API with minimal configuration — often just a DNS change to route traffic through the CDN. You configure caching rules (which paths to cache, for how long) via their dashboard or infrastructure-as-code.

```
Mobile App  ──poll──▶  CDN Edge  ──cache miss──▶  API Server  ──read──▶  Redis
                         │
                         └── cache hit ──▶ (return cached response)
```

At 5 million users polling every 5 seconds, we'd see ~1 million requests per second. But with a 2-second CDN cache TTL:

- The CDN absorbs nearly all requests
- Only a handful of requests per second reach our origin
- Stateless servers scale horizontally with ease
- No WebSocket infrastructure complexity

The tradeoff is latency. With a 2-second cache TTL and clients polling every 3-5 seconds, worst-case latency is ~7 seconds. We specified a 5-second _maximum_, so we'd need to tune these numbers — perhaps a 1-second cache TTL and 3-second polling interval.

**Option D: Hybrid — polling with WebSocket upgrade for active users**

Use polling as the default. When the user is actively viewing the price screen, upgrade to a WebSocket for true real-time updates. When they navigate away, drop back to polling or disconnect entirely.

This limits WebSocket connections to users actively staring at prices, which is a small fraction of 5 million.

### Choosing a Distribution Strategy

For a mobile app, I'd start with **Option C (CDN-backed polling)** for these reasons:

1. **Simplicity** — Stateless HTTP is easier to build, deploy, debug, and scale
2. **Mobile-friendly** — Polling lets the client control frequency based on app state (foreground/background)
3. **Cost-effective** — CDN bandwidth is cheap; WebSocket server memory is not
4. **Good enough** — 3-5 second updates meet the 5-second requirement with margin

If we later find that users want true real-time (sub-second) updates, we can add WebSocket as an enhancement without rearchitecting the system.

## API Design

A single endpoint serves the home screen:

```
GET /api/v1/prices
```

Response:

```json
{
  "prices": [
    { "symbol": "BTC", "price": 67432.15, "change24h": 2.34 },
    { "symbol": "ETH", "price": 3521.8, "change24h": -0.52 },
    { "symbol": "SOL", "price": 142.33, "change24h": 5.12 },
    { "symbol": "XRP", "price": 0.5234, "change24h": 1.02 },
    { "symbol": "DOGE", "price": 0.1542, "change24h": -2.31 }
  ],
  "timestamp": 1706900000000,
  "stale": false
}
```

The `timestamp` is when the backend last received data from upstream. The `stale` flag indicates if data is older than expected (e.g., both sources are down).

Cache headers:

```
Cache-Control: public, max-age=2
```

This tells the CDN to cache for 2 seconds. Clients can cache locally too, but should revalidate frequently.

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA PROVIDERS                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│         Kraken                                  Coinbase                │
│      (WebSocket)                               (REST API)               │
│           │                                        │                    │
└───────────┼────────────────────────────────────────┼────────────────────┘
            │                                        │
            ▼                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         INGESTION SERVICE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│    WebSocket Client ◄─────────────────────► REST Poller (3s)            │
│           │                                        │                    │
│           └──────────────┬─────────────────────────┘                    │
│                          ▼                                              │
│                   ┌─────────────┐                                       │
│                   │ Normalizer  │                                       │
│                   └──────┬──────┘                                       │
│                          ▼                                              │
│                   ┌─────────────┐                                       │
│                   │    Redis    │ ◄── TTL: 10s (auto-expire stale data) │
│                   └─────────────┘                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            API LAYER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│    ┌─────────────┐         ┌─────────────┐         ┌─────────────┐     │
│    │ API Server  │         │ API Server  │         │ API Server  │     │
│    └─────────────┘         └─────────────┘         └─────────────┘     │
│           │                       │                       │             │
│           └───────────────────────┼───────────────────────┘             │
│                                   │                                     │
│                          (read from Redis)                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              CDN                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│    Cache TTL: 2 seconds                                                 │
│    Edge locations worldwide                                             │
│    ~99% of requests served from cache                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         MOBILE CLIENTS                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│    5 million React Native apps                                          │
│    Polling every 3-5 seconds (foreground)                               │
│    Reduced/no polling (background)                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Frontend Architecture

With the backend settled, we can focus on the React Native client.

### State Requirements

The UI needs to track:

- **Price data** — The current prices to display
- **Loading state** — Whether a fetch is in progress
- **Error state** — Whether the last fetch failed (and why)
- **Last updated** — Timestamp of the data (from the API, not when we fetched it)
- **Polling state** — Whether we're actively polling (tied to app foreground/background)

### Data Fetching Strategy

We could use TanStack Query (React Query), which provides:

- Automatic refetching at intervals
- Built-in loading/error states
- Caching and stale-while-revalidate
- Easy pause/resume of polling

Or we could implement polling manually with `useEffect` and `setInterval`. For an interview, I'd mention TanStack Query as the production choice but might implement manually to demonstrate understanding.

### Component Structure

```
<App>
  <HomeScreen>
    <Header />
    <PriceList>
      <PriceCard />  ← repeated for each crypto
      <PriceCard />
      <PriceCard />
      <PriceCard />
      <PriceCard />
    </PriceList>
    <StatusBar>
      <LastUpdated />
      <FetchingIndicator />
    </StatusBar>
    <ErrorBanner />  ← conditional
  </HomeScreen>
</App>
```

### UI States

The home screen has several states to handle:

1. **Initial load** — App just opened, no data yet
2. **Loaded** — Data is displayed, polling continues in background
3. **Refreshing** — New data is being fetched, but we have stale data to show
4. **Error (with cache)** — Fetch failed, but we have previous data
5. **Error (no cache)** — Fetch failed and we have nothing to show
6. **Stale** — Data is older than expected (backend flagged it)
7. **Background** — App is backgrounded, polling paused

### Implementation

Here's a simplified implementation of the data fetching hook:

```typescript
import { useState, useEffect, useRef, useCallback } from "react";
import { AppState, AppStateStatus } from "react-native";

interface PriceData {
  prices: { symbol: string; price: number; change24h: number }[];
  timestamp: number;
  stale: boolean;
}

interface UsePricesResult {
  data: PriceData | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

const POLLING_INTERVAL = 4000; // 4 seconds
const API_URL = "https://api.ourapp.com/v1/prices";

export function usePrices(): UsePricesResult {
  const [data, setData] = useState<PriceData | null>(null);
  const [isLoading, setIsLoading] = useState(true); // true until first successful fetch
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const appStateRef = useRef<AppStateStatus>(AppState.currentState);

  const fetchPrices = useCallback(async () => {
    setIsFetching(true);

    try {
      const response = await fetch(API_URL);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const json: PriceData = await response.json();

      setData(json);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e : new Error("Unknown error"));
      // Don't clear data — keep showing stale data on error
    } finally {
      setIsFetching(false);
      setIsLoading(false);
    }
  }, []);

  // Handle app state changes (foreground/background)
  useEffect(() => {
    const subscription = AppState.addEventListener("change", (nextState) => {
      const wasBackground = appStateRef.current.match(/inactive|background/);
      const isNowForeground = nextState === "active";

      if (wasBackground && isNowForeground) {
        // App came to foreground — fetch immediately and resume polling
        fetchPrices();
        startPolling();
      } else if (nextState.match(/inactive|background/)) {
        // App went to background — stop polling
        stopPolling();
      }

      appStateRef.current = nextState;
    });

    return () => subscription.remove();
  }, [fetchPrices]);

  const startPolling = useCallback(() => {
    if (intervalRef.current) return; // Already polling

    intervalRef.current = setInterval(fetchPrices, POLLING_INTERVAL);
  }, [fetchPrices]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Initial fetch and polling setup
  useEffect(() => {
    fetchPrices();
    startPolling();

    return () => stopPolling();
  }, [fetchPrices, startPolling, stopPolling]);

  return { data, isLoading, isFetching, error, refetch: fetchPrices };
}
```

Key decisions in this implementation:

- **`isLoading` vs `isFetching`** — `isLoading` is true only until the first successful fetch. `isFetching` is true during any fetch. This lets us show a full-screen loader initially, but a subtle indicator during refreshes.
- **Keep stale data on error** — If a fetch fails but we have previous data, we keep showing it. The user sees prices (possibly stale) rather than an error screen.
- **Pause polling when backgrounded** — No point fetching data the user can't see. This saves battery and bandwidth.
- **Fetch immediately on foreground** — When the user returns, we fetch fresh data rather than waiting for the next interval.

### The Home Screen Component

```tsx
import React from "react";
import { View, Text, FlatList, ActivityIndicator, StyleSheet } from "react-native";
import { usePrices } from "./usePrices";
import { PriceCard } from "./PriceCard";
import { formatTimestamp } from "./utils";

export function HomeScreen() {
  const { data, isLoading, isFetching, error } = usePrices();

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Loading prices...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>Unable to refresh prices. Showing last known data.</Text>
        </View>
      )}

      {data?.stale && (
        <View style={styles.warningBanner}>
          <Text style={styles.warningText}>Price data may be delayed.</Text>
        </View>
      )}

      <FlatList
        data={data?.prices ?? []}
        keyExtractor={(item) => item.symbol}
        renderItem={({ item }) => <PriceCard symbol={item.symbol} price={item.price} change24h={item.change24h} />}
        contentContainerStyle={styles.list}
      />

      <View style={styles.statusBar}>
        {data && <Text style={styles.timestamp}>Updated {formatTimestamp(data.timestamp)}</Text>}
        {isFetching && <ActivityIndicator size="small" style={styles.fetchingIndicator} />}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
  },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  loadingText: {
    marginTop: 12,
    color: "#666",
  },
  errorBanner: {
    backgroundColor: "#fee",
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#fcc",
  },
  errorText: {
    color: "#c00",
    textAlign: "center",
  },
  warningBanner: {
    backgroundColor: "#fff3cd",
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#ffc107",
  },
  warningText: {
    color: "#856404",
    textAlign: "center",
  },
  list: {
    padding: 16,
  },
  statusBar: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: "#eee",
  },
  timestamp: {
    color: "#666",
    fontSize: 12,
  },
  fetchingIndicator: {
    marginLeft: 8,
  },
});
```

### The Price Card Component

```tsx
import React from "react";
import { View, Text, StyleSheet } from "react-native";

interface PriceCardProps {
  symbol: string;
  price: number;
  change24h: number;
}

export function PriceCard({ symbol, price, change24h }: PriceCardProps) {
  const isPositive = change24h >= 0;

  return (
    <View style={styles.card}>
      <View style={styles.left}>
        <Text style={styles.symbol}>{symbol}</Text>
      </View>
      <View style={styles.right}>
        <Text style={styles.price}>${formatPrice(price)}</Text>
        <Text style={[styles.change, isPositive ? styles.positive : styles.negative]}>
          {isPositive ? "+" : ""}
          {change24h.toFixed(2)}%
        </Text>
      </View>
    </View>
  );
}

function formatPrice(price: number): string {
  if (price >= 1) {
    return price.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
  // For prices under $1, show more decimal places
  return price.toLocaleString(undefined, {
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  });
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#f8f9fa",
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
  },
  left: {
    flexDirection: "row",
    alignItems: "center",
  },
  symbol: {
    fontSize: 18,
    fontWeight: "600",
  },
  right: {
    alignItems: "flex-end",
  },
  price: {
    fontSize: 18,
    fontWeight: "600",
  },
  change: {
    fontSize: 14,
    marginTop: 4,
  },
  positive: {
    color: "#28a745",
  },
  negative: {
    color: "#dc3545",
  },
});
```

## Error Handling Strategy

Errors can occur at multiple points. Here's how we handle each:

### Backend: Upstream Provider Failure

If Kraken's WebSocket disconnects:

1. Mark Kraken source as "down" in metadata
2. Continue serving data from Coinbase
3. Attempt reconnection with exponential backoff
4. If reconnection succeeds, resume normal operation

If Coinbase API returns errors:

1. Mark Coinbase source as "down" in metadata
2. Continue serving data from Kraken
3. Retry on next polling interval

If both are down:

1. Set `stale: true` in API response
2. Continue serving cached data (with increasingly old timestamp)
3. Frontend displays "data may be delayed" warning

### Backend: Redis Failure

API servers should handle Redis being unavailable:

1. Return 503 with `Retry-After` header
2. CDN continues serving cached responses until TTL expires
3. Frontend shows error but keeps displaying last known data

### Frontend: Network Errors

If `fetch` fails:

1. Keep previous data in state (don't clear it)
2. Set error state to show banner
3. Continue polling — network may recover
4. On successful fetch, clear error state

### Frontend: Malformed Data

If API returns unexpected data:

1. Validate response shape before updating state
2. If validation fails, treat as an error
3. Log the issue for debugging
4. Don't update UI with bad data

```typescript
function isValidPriceData(data: unknown): data is PriceData {
  if (typeof data !== "object" || data === null) return false;

  const obj = data as Record<string, unknown>;

  if (!Array.isArray(obj.prices)) return false;
  if (typeof obj.timestamp !== "number") return false;

  return obj.prices.every(
    (p) =>
      typeof p === "object" &&
      p !== null &&
      typeof (p as Record<string, unknown>).symbol === "string" &&
      typeof (p as Record<string, unknown>).price === "number" &&
      (p as Record<string, unknown>).price > 0,
  );
}
```

## Scaling Considerations

### CDN Configuration

The CDN is the critical piece for handling 5 million users. Configuration:

- **Cache TTL**: 2 seconds (balances freshness with cache hit rate)
- **Stale-while-revalidate**: 10 seconds (serve stale while fetching fresh)
- **Edge locations**: Global distribution for low latency
- **Cache key**: Just the URL path (no query params, no cookies)

Expected cache hit rate: >99%. At 1 million requests per second, fewer than 10,000 would reach origin.

### API Server Scaling

With the CDN absorbing most traffic, the API servers see minimal load. A small cluster (3-5 instances) behind a load balancer provides redundancy without overprovisioning.

Each request is a simple Redis read — no computation, no database queries. Servers can be small and cheap.

### Ingestion Service Scaling

The ingestion service maintains exactly one WebSocket connection to Kraken and polls Coinbase at a fixed interval. It doesn't need to scale horizontally — but it does need redundancy.

Run 2-3 instances with leader election. Only the leader connects to upstream and writes to Redis. If the leader fails, another instance takes over. This prevents duplicate data or conflicting writes.

### Redis Configuration

A single Redis instance is likely sufficient (prices for 5 cryptos is tiny). For redundancy:

- Use Redis Sentinel or Redis Cluster
- Configure appropriate memory limits
- Set TTLs on all keys to prevent unbounded growth

## What We'd Add in Production

Given more time, these improvements would make the system more robust:

**Circuit breakers** — If an upstream provider fails repeatedly, stop hammering it. Back off and recover gracefully.

**Monitoring and alerting** — Track latency, error rates, cache hit ratios. Alert on anomalies.

**Request tracing** — Correlate requests across CDN, API servers, and ingestion service for debugging.

**Rate limiting** — Protect the API from abusive clients (even with a CDN, origin still needs protection).

**A/B testing infrastructure** — For testing different polling intervals, UI treatments, etc.

**Offline support** — Cache the last known prices in AsyncStorage so the app isn't blank on launch with no network.

**Push notifications** — For significant price movements, notify users even when the app is closed.

**WebSocket upgrade path** — For power users who want sub-second updates, offer an optional WebSocket connection.

## Summary

The key insights from this exercise:

1. **The backend is unavoidable.** Direct client connections to upstream APIs don't scale. A backend aggregates data as a single well-behaved client and distributes it to millions.

2. **Stateless scales better.** CDN-backed REST polling is simpler and cheaper than WebSocket at this scale. The 5-second requirement doesn't demand true real-time.

3. **Graceful degradation everywhere.** Every component fails eventually. Keep showing data (even stale data) as long as possible.

4. **Mobile constraints matter.** Battery life and network variability mean aggressive polling isn't always appropriate. Respect app lifecycle states.

5. **Start simple, measure, iterate.** The polling approach is easy to build and deploy. If users demand faster updates, we can add WebSocket support later without rearchitecting.

The architecture we designed handles 5 million users with a surprisingly small backend footprint — because the CDN does the heavy lifting, and we made choices that minimize complexity at each layer.
