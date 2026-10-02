// Dependency-free JavaScript example using plain fetch (Node >= 20 or browser).
//
//   node examples/javascript/fetch-example.mjs http://localhost:8000 "<raw initData>"
//
// For local development, generate initData with:
//   python -c "from examples.python.miniapp_client import sign_init_data; print(sign_init_data('<TELEGRAM_BOT_TOKEN>'))"

export async function miniAppRequest(baseUrl, initData, path, { method = "GET", body, fetchImpl = fetch } = {}) {
  const response = await fetchImpl(`${baseUrl.replace(/\/+$/, "")}/v1/miniapp${path}`, {
    method,
    headers: { "Content-Type": "application/json", "X-Telegram-Init-Data": initData },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (response.status === 204) return undefined;
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof payload?.detail === "string" ? payload.detail : "Request failed";
    const error = new Error(`${response.status}: ${detail}`);
    error.status = response.status;
    error.detail = detail;
    throw error;
  }
  return payload;
}

export async function runExample(baseUrl, initData, fetchImpl = fetch) {
  const call = (path, options = {}) => miniAppRequest(baseUrl, initData, path, { ...options, fetchImpl });
  const bootstrap = await call("/bootstrap");
  const delivery = await call("/assist/decode", {
    method: "POST",
    body: { text: "Сейчас не до этого", relationship_id: bootstrap.user.default_relationship_id, language: "ru" },
  });
  return { userId: bootstrap.user.user_id, status: delivery.status, text: delivery.text };
}

const isMain = typeof process !== "undefined" && process.argv[1]?.endsWith("fetch-example.mjs");
if (isMain) {
  const [baseUrl = "http://localhost:8000", initData = process.env.TELEGRAM_INIT_DATA] = process.argv.slice(2);
  if (!initData) {
    console.error("Pass raw initData as the second argument or TELEGRAM_INIT_DATA.");
    process.exit(1);
  }
  runExample(baseUrl, initData).then(
    (result) => console.log(JSON.stringify(result, null, 2)),
    (error) => {
      console.error(error.message);
      process.exit(1);
    },
  );
}
