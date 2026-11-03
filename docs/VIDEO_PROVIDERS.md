# Video providers

The local settings screen stores API keys on the server, encrypted with Windows DPAPI for the current Windows user. `VIDEO_SETTINGS_PATH` overrides the default `video-providers.json` beside `DATABASE_PATH`. Back up the encrypted file with the Windows user profile; copying it to another account does not transfer credentials. API responses show only whether a key exists. Environment Ark credentials remain a fallback, and deleting a saved override does not erase environment variables.

Endpoints are fixed. Fireworks/custom proxy URLs are not accepted. Keys must match the vendor/region. The Ark model IDs continue to use ARK_MODEL_ID and ARK_FAST_MODEL_ID. Without saved activation the existing VIDEO_PROVIDER/ARK_API_KEY behavior is preserved, including mock mode.

Configuration writes require a local client, a trusted localhost Host and same-origin browser requests; key updates additionally require JSON. This is a local single-user administration interface. These checks are not multiuser authentication: deploy behind authentication and authorization before exposing the application to other users or a network. Do not trust forwarded headers from arbitrary clients.

Connection tests only list metadata/account information and never submit a generation. They do not establish model entitlement or sufficient balance. No paid vendor calls were used in automated tests. Local credit estimates are application accounting estimates, not vendor quotations.

Tasks persist their original provider. Switching does not redirect polling; replacement/deletion of keys is blocked while that provider has active tasks. Active credentials cannot be deleted until another provider is selected. Wan and Luma cancellation is rejected explicitly; a submitted request may still incur vendor charges.

The UI exposes only the intersection of vendor support and this application's input schema. Unsupported parameters are rejected before credit reservation. Runway Gen-4.5 supports text-to-video landscape/portrait at 720p without audio. Luma uses ray-flash-2 for fast quality and ray-2 otherwise, with 5-second generation exposed. Wan uses wan2.6-t2v on DashScope Beijing and always generates audio (`requiresAudio: true`); disabling audio is rejected. Non-Ark estimates use a standard local quota factor; quality is not a Wan/Runway model switch. Ark retains its existing fast/standard model selection.

Official references checked 2026-10-30:

- [Runway inputs](https://docs.dev.runwayml.com/assets/inputs/), [API guide](https://docs.dev.runwayml.com/guides/using-the-api/)
- [Luma video generation](https://docs.lumalabs.ai/docs/video-generation), [create generation](https://docs.lumalabs.ai/reference/creategeneration)
- [Wan text-to-video reference](https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference) (legacy Beijing domain remains supported; this integration uses the wan2.6 protocol).
