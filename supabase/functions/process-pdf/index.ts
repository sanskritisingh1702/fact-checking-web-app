import "jsr:@supabase/functions-js/edge-runtime.d.ts"
// @ts-ignore
import * as pdfjsLib from "npm:pdfjs-dist@4.4.168/build/pdf.mjs"

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
}

// ─── Claim extraction patterns ───────────────────────────────────────────────

type ClaimType =
  | "Statistic"
  | "Date/Temporal"
  | "Financial/Monetary"
  | "Technical/Specification"
  | "Percentage/Ratio"
  | "General Fact"

interface ExtractedClaim {
  text: string
  claim_type: ClaimType
  source_text: string
  page_number: number
}

const PATTERNS: Record<ClaimType, RegExp[]> = {
  "Financial/Monetary": [
    /\$\s?\d[\d,]*(?:\.\d+)?(?:\s*(?:million|billion|trillion|M|B|T))?(?:\s+(?:USD|dollars?))?\b/gi,
    /\b\d[\d,]*(?:\.\d+)?\s*(?:million|billion|trillion)\s*(?:USD|EUR|GBP|dollars?|euros?|pounds?)?\b/gi,
    /\b(?:revenue|profit|loss|sales|earnings|valuation|market cap)\s+(?:of\s+)?\$?\s?\d[\d,]*(?:\.\d+)?(?:\s*(?:million|billion|trillion|M|B))?\b/gi,
  ],
  "Statistic": [
    /\b\d[\d,]*(?:\.\d+)?\s*(?:million|billion|trillion)?\s*(?:users?|customers?|people|employees?|subscribers?|units?|cases?|deaths?|infections?|accounts?)\b/gi,
    /\b(?:total|approximately|around|about|over|more than|nearly|up to)\s+\d[\d,]*(?:\.\d+)?(?:\s*(?:million|billion))?/gi,
    /\b\d[\d,]*\s*(?:km|km²|sq km|miles?|acres?|hectares?|sq ft)\b/gi,
  ],
  "Percentage/Ratio": [
    /\b\d{1,3}(?:\.\d+)?%(?:\s+of\s+\w+)?\b/gi,
    /\b\d{1,3}(?:\.\d+)?\s+percent(?:age)?\b/gi,
    /\b(?:increased?|decreased?|grew|grew by|fell by|declined?|surged?|jumped?|dropped?)\s+(?:by\s+)?\d{1,3}(?:\.\d+)?%\b/gi,
  ],
  "Date/Temporal": [
    /\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(?:19|20)\d{2}\b/gi,
    /\b(?:in|since|from|during|as of|by)\s+(?:19|20)\d{2}\b/gi,
    /\b(?:Q[1-4]|first|second|third|fourth)\s+(?:quarter)\s+(?:of\s+)?(?:19|20)\d{2}\b/gi,
    /\b(?:founded|established|launched|created|opened)\s+in\s+(?:19|20)\d{2}\b/gi,
  ],
  "Technical/Specification": [
    /\b\d+(?:\.\d+)?\s*(?:GHz|MHz|TB|GB|MB|KB|nm|nanometer|Gbps|Mbps|kWh|MW|GW)\b/gi,
    /\b\d+(?:\.\d+)?\s*-?\s*(?:inch|mm|cm|meter|kg|lb|watt|volt|amp)\b/gi,
    /\bversion\s+\d+(?:\.\d+)+/gi,
  ],
  "General Fact": [
    /\b(?:headquartered?|based|located)\s+in\s+[A-Z][a-z]+(?:[\s,]+[A-Z][a-z]+)*\b/g,
    /\b(?:CEO|founder|president|chairman|director)\s+(?:is|was|and)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+/g,
    /\b(?:acquired|bought|purchased|merged with)\s+(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b/g,
  ],
}

function extractClaims(text: string, pageNumber: number): ExtractedClaim[] {
  const seen = new Set<string>()
  const claims: ExtractedClaim[] = []

  for (const [type, patterns] of Object.entries(PATTERNS)) {
    for (const pattern of patterns) {
      pattern.lastIndex = 0
      let match: RegExpExecArray | null
      while ((match = pattern.exec(text)) !== null) {
        const raw = match[0].trim()
        if (!raw || raw.length < 3) continue

        const key = raw.toLowerCase()
        if (seen.has(key)) continue
        seen.add(key)

        const start = Math.max(0, match.index - 120)
        const end = Math.min(text.length, match.index + raw.length + 120)
        const context = text.slice(start, end).trim()

        claims.push({
          text: raw,
          claim_type: type as ClaimType,
          source_text: context,
          page_number: pageNumber,
        })
      }
    }
  }

  return claims
}

// ─── PDF text extraction ─────────────────────────────────────────────────────

async function extractTextFromPDF(bytes: Uint8Array): Promise<{ page: number; text: string }[]> {
  const loadingTask = pdfjsLib.getDocument({ data: bytes })
  const pdfDoc = await loadingTask.promise

  const pages: { page: number; text: string }[] = []

  for (let i = 1; i <= pdfDoc.numPages; i++) {
    const page = await pdfDoc.getPage(i)
    const content = await page.getTextContent()
    const text = content.items
      .filter((item: { str?: string }) => "str" in item)
      .map((item: { str?: string }) => item.str ?? "")
      .join(" ")
      .replace(/\s+/g, " ")
      .trim()

    if (text.length > 0) {
      pages.push({ page: i, text })
    }
  }

  return pages
}

// ─── Handler ─────────────────────────────────────────────────────────────────

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders })
  }

  try {
    const contentType = req.headers.get("content-type") ?? ""

    let pdfBytes: Uint8Array

    if (contentType.includes("multipart/form-data")) {
      const form = await req.formData()
      const file = form.get("file")
      if (!file || !(file instanceof File)) {
        return Response.json({ error: "No PDF file found in form data" }, { status: 400, headers: corsHeaders })
      }
      const buf = await file.arrayBuffer()
      pdfBytes = new Uint8Array(buf)
    } else {
      const buf = await req.arrayBuffer()
      pdfBytes = new Uint8Array(buf)
    }

    if (pdfBytes.length === 0) {
      return Response.json({ error: "Empty file" }, { status: 400, headers: corsHeaders })
    }

    const pages = await extractTextFromPDF(pdfBytes)
    if (pages.length === 0) {
      return Response.json({ error: "Could not extract text. Ensure PDF has selectable text (not a scanned image)." }, { status: 422, headers: corsHeaders })
    }

    const allClaims: ExtractedClaim[] = []
    for (const { page, text } of pages) {
      const pageClaims = extractClaims(text, page)
      allClaims.push(...pageClaims)
    }

    // Deduplicate and limit to 40 most interesting claims
    const seen = new Set<string>()
    const unique = allClaims.filter(c => {
      const k = c.text.toLowerCase()
      if (seen.has(k)) return false
      seen.add(k)
      return true
    })

    // Prioritize by type
    const priority: Record<ClaimType, number> = {
      "Financial/Monetary": 1,
      "Statistic": 2,
      "Percentage/Ratio": 3,
      "Technical/Specification": 4,
      "Date/Temporal": 5,
      "General Fact": 6,
    }
    unique.sort((a, b) => (priority[a.claim_type] ?? 9) - (priority[b.claim_type] ?? 9))

    return Response.json(
      { claims: unique.slice(0, 40), page_count: pages.length },
      { headers: corsHeaders }
    )
  } catch (err) {
    console.error("process-pdf error:", err)
    return Response.json(
      { error: err instanceof Error ? err.message : "Internal server error" },
      { status: 500, headers: corsHeaders }
    )
  }
})
