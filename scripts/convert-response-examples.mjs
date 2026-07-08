#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

function printUsage() {
  console.log(`Usage:
  node scripts/convert-response-examples.mjs [input.json] [--output output.json] [--dry-run]

Defaults:
  input.json: toopen.json
  output.json: same as input.json

Description:
  Converts JSON strings found under OpenAPI responses into JSON objects or arrays.
`);
}

function parseArgs(argv) {
  const args = {
    input: "toopen.json",
    output: null,
    dryRun: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === "--help" || arg === "-h") {
      args.help = true;
      continue;
    }

    if (arg === "--dry-run") {
      args.dryRun = true;
      continue;
    }

    if (arg === "--output" || arg === "-o") {
      const next = argv[index + 1];
      if (!next) {
        throw new Error(`${arg} requires a file path`);
      }
      args.output = next;
      index += 1;
      continue;
    }

    if (arg.startsWith("-")) {
      throw new Error(`Unknown option: ${arg}`);
    }

    args.input = arg;
  }

  args.output ??= args.input;
  return args;
}

function parseJsonString(value) {
  const trimmed = value.trim();

  if (!trimmed.startsWith("{") && !trimmed.startsWith("[")) {
    return { converted: false, value };
  }

  try {
    const parsed = JSON.parse(trimmed);
    if (parsed !== null && typeof parsed === "object") {
      return { converted: true, value: parsed };
    }
  } catch {
    return { converted: false, value };
  }

  return { converted: false, value };
}

function convertResponseStrings(value, context = { inResponses: false, path: [] }, changes = []) {
  if (typeof value === "string") {
    if (!context.inResponses) {
      return value;
    }

    const result = parseJsonString(value);
    if (result.converted) {
      changes.push(context.path.join("."));
    }
    return result.value;
  }

  if (Array.isArray(value)) {
    return value.map((item, index) =>
      convertResponseStrings(
        item,
        {
          inResponses: context.inResponses,
          path: [...context.path, String(index)],
        },
        changes,
      ),
    );
  }

  if (value && typeof value === "object") {
    const converted = {};
    for (const [key, child] of Object.entries(value)) {
      converted[key] = convertResponseStrings(
        child,
        {
          inResponses: context.inResponses || key === "responses",
          path: [...context.path, key],
        },
        changes,
      );
    }
    return converted;
  }

  return value;
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    printUsage();
    return;
  }

  const inputPath = path.resolve(args.input);
  const outputPath = path.resolve(args.output);
  const raw = fs.readFileSync(inputPath, "utf8");
  const document = JSON.parse(raw);
  const changes = [];
  const converted = convertResponseStrings(document, undefined, changes);

  if (args.dryRun) {
    console.log(`Found ${changes.length} response JSON string(s) to convert.`);
    for (const changedPath of changes) {
      console.log(`- ${changedPath}`);
    }
    return;
  }

  fs.writeFileSync(outputPath, `${JSON.stringify(converted, null, 2)}\n`, "utf8");
  console.log(`Converted ${changes.length} response JSON string(s).`);
  console.log(`Wrote ${outputPath}`);
}

try {
  main();
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
}
