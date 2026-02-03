import type { Config } from "knowhub";

const GITHUB_RAW_BASE = "https://raw.githubusercontent.com/JEM-Fizbit/ai-knowledge/main/protocols";

const config: Config = {
  resources: [
    // Claude Code differences
    {
      plugin: "http",
      pluginConfig: { url: `${GITHUB_RAW_BASE}/CLAUDE_CODE_WEB_VS_TERMINAL.md` },
      overwrite: true,
      outputs: ["docs/protocols/CLAUDE_CODE_WEB_VS_TERMINAL.md"],
    },
    // Git Conventions
    {
      plugin: "http",
      pluginConfig: { url: `${GITHUB_RAW_BASE}/GIT_CONVENTIONS.md` },
      overwrite: true,
      outputs: ["docs/protocols/GIT_CONVENTIONS.md"],
    },
  ],
};

export default config;
