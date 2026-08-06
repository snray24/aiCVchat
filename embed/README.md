# Embeddable AiCV Chat Widget

Standalone JavaScript widget to embed the resume chatbot on **any authorized website**.  
It does **not** use the Next.js frontend — only the FastAPI chat API.

**Abuse protection (domain keys + session tokens):** see [ABUSE_PROTECTION.md](./ABUSE_PROTECTION.md) for structure, flow, files added/modified, impact, and how to use.

UI colors follow the [eMasters acquire-talent](https://emasters-acquire-talent.sanjalenterprises.com/) brand.

## Abuse protection (required)

Unauthorized embeds are blocked by default (`EMBED_AUTH_REQUIRED=true`):

1. **Register** the host domain (admin API or CLI) → unique `site_key`
2. **Install** loader with `?key=SITE_KEY`
3. Widget calls `POST /api/embed/session` (Origin must match registered domain / optional IP allowlist)
4. Chat/search require `Authorization: Bearer <short-lived token>` (HMAC, ~10 min TTL)
5. **Rate limits** per IP and per site key
6. **Dynamic CORS** only for `FRONTEND_ORIGIN` + registered domains (not `*` unless emergency flag)
7. **HTTPS** required when `APP_ENV=production` (or `EMBED_REQUIRE_HTTPS=true`)

Site keys in HTML are public; security is domain/IP binding + short tokens + rate limits + TLS.

### Register a domain

```bash
cd backend
python scripts/register_embed_site.py --name "Acme Careers" --domain careers.acme.com
# optional: --allow-subdomains --allowed-ip 203.0.113.10
```

Or:

```bash
curl -X POST http://localhost:8000/api/admin/embed-sites \
  -H "X-Admin-Token: $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme","domain":"careers.acme.com","allow_subdomains":false}'
```

Admin also supports list / revoke / rotate-key under `/api/admin/embed-sites`.

### One-liner snippet

```html
<script src="https://YOUR-API-HOST/embed/loader.js?key=aicv_YOUR_KEY" async></script>
```

Generate with host filled in:

- `GET /api/embed/snippet?key=aicv_…`
- UI: `/embed/snippet.html?key=…`
- Demo: `/embed/demo.html?key=…`

## Features

- Shadow DOM isolation
- Responsive (full-screen on small devices)
- Timestamps, typing + spinner, sent/delivered/read ticks
- Candidate match cards
- Auto API base from loader / script origin
- Domain-bound session auth

## Configuration (`AiCVChatConfig`)

| Key | Default | Purpose |
|-----|---------|---------|
| `apiBaseUrl` | `""` (auto) | API origin |
| `siteKey` | `""` | From registration (or loader `?key=`) |
| `sessionPath` | `/api/embed/session` | Session endpoint |
| `chatPath` | `/api/chat` | Chat endpoint |
| `position` | `right` | `right` \| `left` |
| `openOnLoad` | `false` | Open on load |
| `showMatches` | `true` | Candidate cards |
| `historyLimit` | `12` | History cap |
| `requestTimeoutMs` | `120000` | Abort slow LLM |
| `zIndex` | `2147483000` | Stacking |

## Backend env (see `backend/.env.example`)

| Var | Role |
|-----|------|
| `EMBED_AUTH_REQUIRED` | Gate chat/search (default `true`) |
| `EMBED_TOKEN_SECRET` | HMAC secret for session tokens |
| `EMBED_TOKEN_TTL_SECONDS` | Token lifetime (default 600) |
| `EMBED_RATE_LIMIT_PER_MINUTE` | Per-IP limit |
| `EMBED_SITE_RATE_LIMIT_PER_MINUTE` | Per-site limit |
| `EMBED_REQUIRE_HTTPS` | Force HTTPS (default: on in production) |
| `CORS_ALLOW_ANY_ORIGIN` | Emergency `*` CORS only |
| `FRONTEND_ORIGIN` | Always-allowed origins (Next app, etc.) |

## Next.js app

Set `NEXT_PUBLIC_EMBED_SITE_KEY` after registering `localhost` (or your front-end host).  
`frontend/lib/embedAuth.ts` attaches the Bearer token to chat/search.

Break-glass for local-only: `EMBED_AUTH_REQUIRED=false` (not for production).

## Rate limiting note

In-process sliding windows suit a single-machine deploy. For multi-instance production, replace with Redis (same key scheme: `ip:…` / `site:…`).

## License

Same as the parent repository.
