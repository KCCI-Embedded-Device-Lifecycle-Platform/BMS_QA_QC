import fs from "node:fs/promises";
import path from "node:path";

import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const outputDir = path.join(root, "outputs", "qa_aspice_framework");
const manifest = JSON.parse(
  await fs.readFile(path.join(root, "docs", "jira_export", "test_case_manifest.json"), "utf8"),
);

await fs.mkdir(outputDir, { recursive: true });

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const rtm = workbook.worksheets.add("RTM");
const requirements = workbook.worksheets.add("Requirements");
const openItems = workbook.worksheets.add("Open_Items");
const legend = workbook.worksheets.add("Legend");
const traceMap = workbook.worksheets.add("Trace_Map");

const navy = "#16324F";
const teal = "#0E7490";
const lightTeal = "#DDF3F5";
const amber = "#F59E0B";
const lightAmber = "#FFF3CD";
const red = "#B91C1C";
const lightRed = "#FEE2E2";
const green = "#15803D";
const lightGreen = "#DCFCE7";
const gray = "#E5E7EB";
const darkGray = "#475569";

function title(sheet, range, text) {
  sheet.getRange(range).merge();
  const cell = sheet.getRange(range.split(":")[0]);
  cell.values = [[text]];
  cell.format = {
    fill: navy,
    font: { bold: true, color: "#FFFFFF", size: 16 },
    verticalAlignment: "center",
  };
  sheet.getRange(range).format.rowHeight = 30;
}

function header(range) {
  range.format = {
    fill: teal,
    font: { bold: true, color: "#FFFFFF" },
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "medium", color: navy },
  };
}

for (const sheet of [summary, rtm, requirements, openItems, legend, traceMap]) {
  sheet.showGridLines = false;
}

// Summary
title(summary, "A1:K1", "BMS–EVSE–OTA ASPICE Traceability Dashboard");
summary.getRange("A2:K2").merge();
summary.getRange("A2").values = [[
  "QA baseline: Reviewed Final 54 cases | READY means automation readiness, not a PASS verdict",
]];
summary.getRange("A2").format = {
  fill: "#E2E8F0",
  font: { italic: true, color: darkGray },
  wrapText: true,
};

summary.getRange("A4:B4").merge();
summary.getRange("D4:E4").merge();
summary.getRange("G4:H4").merge();
summary.getRange("J4:K4").merge();
summary.getRange("A4").values = [["TOTAL TESTS"]];
summary.getRange("D4").values = [["P0 TESTS"]];
summary.getRange("G4").values = [["REQUIREMENT GAPS"]];
summary.getRange("J4").values = [["CONTRACT WAITING"]];
for (const range of ["A4:B4", "D4:E4", "G4:H4", "J4:K4"]) {
  summary.getRange(range).format = {
    fill: teal,
    font: { bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
  };
}
summary.getRange("A5:B7").merge();
summary.getRange("D5:E7").merge();
summary.getRange("G5:H7").merge();
summary.getRange("J5:K7").merge();
summary.getRange("A5").formulas = [["=COUNTA(RTM!$A$5:$A$58)"]];
summary.getRange("D5").formulas = [["=COUNTIF(RTM!$F$5:$F$58,\"P0\")"]];
summary.getRange("G5").formulas = [["=COUNTIF(RTM!$I$5:$I$58,\"GAP_REQUIREMENT\")"]];
summary.getRange("J5").formulas = [["=COUNTIF(RTM!$I$5:$I$58,\"CONTRACT_WAITING\")"]];
for (const range of ["A5:B7", "D5:E7", "G5:H7", "J5:K7"]) {
  summary.getRange(range).format = {
    fill: "#F8FAFC",
    font: { bold: true, color: navy, size: 24 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "outside", style: "medium", color: "#CBD5E1" },
  };
}
summary.getRange("G5:H7").format.fill = lightAmber;
summary.getRange("J5:K7").format.fill = lightRed;

summary.getRange("A10:K10").merge();
summary.getRange("A10").values = [["Qualification statement"]];
summary.getRange("A10").format = { fill: navy, font: { bold: true, color: "#FFFFFF" } };
summary.getRange("A11:K11").merge();
summary.getRange("A11").values = [[
  "Formal PASS requires product SHA + ELF/BIN SHA-256 + OpenOCD verify_image + required physical oracle. Current workbook is NOT EXECUTED.",
]];
summary.getRange("A11").format = { fill: lightAmber, font: { color: "#7C2D12" }, wrapText: true };

summary.getRange("A14:B14").values = [["Disposition", "Count"]];
summary.getRange("A15:A18").values = [
  ["READY"],
  ["READY_HIL_CONDITIONAL"],
  ["GAP_REQUIREMENT"],
  ["CONTRACT_WAITING"],
];
summary.getRange("B15").formulas = [["=COUNTIF(RTM!$I$5:$I$58,A15)"]];
summary.getRange("B15:B18").fillDown();
header(summary.getRange("A14:B14"));
summary.getRange("A15:B18").format.borders = {
  preset: "inside",
  style: "thin",
  color: gray,
};
const dispositionChart = summary.charts.add("bar", summary.getRange("A14:B18"));
dispositionChart.title = "Test readiness by disposition";
dispositionChart.hasLegend = false;
dispositionChart.setPosition("D13", "K26");

summary.getRange("A29:K29").merge();
summary.getRange("A29").values = [["Open quality gates"]];
summary.getRange("A29").format = { fill: red, font: { bold: true, color: "#FFFFFF" } };
summary.getRange("A30:K33").values = [
  ["1", "EVSE linker currently reaches 0x08200000 and overlaps the approved OTA staging boundary at 0x08100000.", null, null, null, null, null, null, null, null, null],
  ["2", "BMS 1000 ms link requirement may be delayed by common three-sample fault confirmation; HIL must classify the deviation.", null, null, null, null, null, null, null, null, null],
  ["3", "OTA version, rollback and target binding are requirement/product gaps.", null, null, null, null, null, null, null, null, null],
  ["4", "Gateway tests remain contract-waiting until its source boundary and schema are approved.", null, null, null, null, null, null, null, null, null],
];
for (let row = 30; row <= 33; row += 1) {
  summary.getRange(`B${row}:K${row}`).merge();
}
summary.getRange("A30:K33").format = { fill: "#FFF7ED", wrapText: true };
summary.getRange("A30:A33").format = {
  font: { bold: true, color: red },
  horizontalAlignment: "center",
};
summary.getRange("A1:K33").format.font.name = "Aptos";
summary.getRange("A:A").format.columnWidth = 24;
summary.getRange("B:B").format.columnWidth = 12;
summary.getRange("C:C").format.columnWidth = 3;
summary.getRange("D:K").format.columnWidth = 14;
summary.getRange("A30:K33").format.rowHeight = 30;
summary.freezePanes.freezeRows(2);

// RTM
title(rtm, "A1:O1", "Requirements Traceability Matrix — 54 Jira Tests");
rtm.getRange("A2:O2").merge();
rtm.getRange("A2").values = [[
  "Execution Result and Evidence Link are editable. Disposition is design readiness and shall not be used as the execution verdict.",
]];
rtm.getRange("A2").format = { fill: lightAmber, font: { color: "#7C2D12" }, wrapText: true };
const rtmHeaders = [
  "Test ID",
  "Area",
  "Summary",
  "Requirement ID",
  "ASPICE",
  "Priority",
  "Level",
  "Method",
  "Disposition",
  "Automation",
  "Precondition",
  "Expected Independent Oracle",
  "Execution Result",
  "Evidence Link",
  "Reviewer",
];
rtm.getRange("A4:O4").values = [rtmHeaders];
header(rtm.getRange("A4:O4"));
const rtmRows = manifest.cases.map((item) => [
  item.test_id,
  item.area,
  item.summary,
  item.requirement_id,
  item.aspice,
  item.priority,
  item.level,
  item.method,
  item.disposition,
  item.automation,
  item.precondition,
  item.expected,
  "NOT_EXECUTED",
  "",
  "",
]);
rtm.getRange("A5:O58").values = rtmRows;
const rtmTable = rtm.tables.add("A4:O58", true, "RTMTable");
rtmTable.style = "TableStyleMedium2";
rtmTable.showBandedRows = true;
rtm.getRange("A5:O58").format = { verticalAlignment: "top", wrapText: true };
rtm.getRange("A:A").format.columnWidth = 22;
rtm.getRange("B:B").format.columnWidth = 11;
rtm.getRange("C:C").format.columnWidth = 30;
rtm.getRange("D:D").format.columnWidth = 28;
rtm.getRange("E:F").format.columnWidth = 10;
rtm.getRange("G:I").format.columnWidth = 20;
rtm.getRange("J:J").format.columnWidth = 38;
rtm.getRange("K:L").format.columnWidth = 44;
rtm.getRange("M:O").format.columnWidth = 22;
rtm.getRange("A5:O58").format.rowHeight = 45;
rtm.getRange("M5:M58").dataValidation = {
  rule: {
    type: "list",
    values: [
      "NOT_EXECUTED",
      "PASS",
      "FAIL_PRODUCT",
      "GAP_REQUIREMENT",
      "FAIL_TEST",
      "BLOCKED_INFRA",
      "MISMATCH_CONFIGURATION",
      "NOT_APPLICABLE",
    ],
  },
};
rtm.getRange("I5:I58").conditionalFormats.add("containsText", {
  text: "GAP",
  format: { fill: lightAmber, font: { color: "#7C2D12", bold: true } },
});
rtm.getRange("I5:I58").conditionalFormats.add("containsText", {
  text: "CONTRACT_WAITING",
  format: { fill: lightRed, font: { color: red, bold: true } },
});
rtm.getRange("M5:M58").conditionalFormats.add("containsText", {
  text: "PASS",
  format: { fill: lightGreen, font: { color: green, bold: true } },
});
rtm.getRange("M5:M58").conditionalFormats.add("containsText", {
  text: "FAIL",
  format: { fill: lightRed, font: { color: red, bold: true } },
});
rtm.getRange("M5:M58").conditionalFormats.add("containsText", {
  text: "BLOCKED",
  format: { fill: lightAmber, font: { color: "#7C2D12", bold: true } },
});
rtm.freezePanes.freezeRows(4);
rtm.freezePanes.freezeColumns(2);

// Requirements coverage
title(requirements, "A1:F1", "SWRS Coverage Index");
requirements.getRange("A3:F3").values = [[
  "Requirement ID",
  "Area",
  "Linked Tests",
  "P0 Tests",
  "Coverage State",
  "Review Note",
]];
header(requirements.getRange("A3:F3"));
const requirementIds = [
  ...new Set(
    manifest.cases.flatMap((item) => item.requirement_id.split(",").map((value) => value.trim())),
  ),
].sort();
const requirementRows = requirementIds.map((id) => [
  id,
  id.split("-")[1],
  null,
  null,
  null,
  id === "SWRS-GA-001" ? "Contract waiting" : "See SWRS.md for SHALL statement",
]);
requirements.getRange(`A4:F${3 + requirementRows.length}`).values = requirementRows;
const traceRows = manifest.cases.flatMap((item) =>
  item.requirement_id.split(",").map((requirementId) => [
    requirementId.trim(),
    item.test_id,
    item.priority,
    item.area,
  ]),
);
title(traceMap, "A1:D1", "Normalized Requirement-to-Test Links");
traceMap.getRange("A3:D3").values = [["Requirement ID", "Test ID", "Priority", "Area"]];
header(traceMap.getRange("A3:D3"));
traceMap.getRange(`A4:D${3 + traceRows.length}`).values = traceRows;
const traceTable = traceMap.tables.add(
  `A3:D${3 + traceRows.length}`,
  true,
  "TraceMapTable",
);
traceTable.style = "TableStyleMedium2";
traceMap.getRange("A:A").format.columnWidth = 26;
traceMap.getRange("B:B").format.columnWidth = 24;
traceMap.getRange("C:D").format.columnWidth = 14;
traceMap.freezePanes.freezeRows(3);
requirements.getRange(`C4:C${3 + requirementRows.length}`).formulas = requirementIds.map(
  (id) => [`=COUNTIF(Trace_Map!$A$4:$A$${3 + traceRows.length},\"${id}\")`],
);
requirements.getRange(`D4:D${3 + requirementRows.length}`).formulas = requirementIds.map(
  (id) => [
    `=COUNTIFS(Trace_Map!$A$4:$A$${3 + traceRows.length},\"${id}\",Trace_Map!$C$4:$C$${3 + traceRows.length},\"P0\")`,
  ],
);
requirements.getRange("E4").formulas = [["=IF(C4>0,\"LINKED\",\"MISSING\")"]];
requirements.getRange(`E4:E${3 + requirementRows.length}`).fillDown();
const reqTable = requirements.tables.add(
  `A3:F${3 + requirementRows.length}`,
  true,
  "RequirementCoverageTable",
);
reqTable.style = "TableStyleMedium2";
requirements.getRange(`A4:F${3 + requirementRows.length}`).format = {
  verticalAlignment: "top",
  wrapText: true,
};
requirements.getRange("A:A").format.columnWidth = 24;
requirements.getRange("B:B").format.columnWidth = 12;
requirements.getRange("C:E").format.columnWidth = 16;
requirements.getRange("F:F").format.columnWidth = 38;
requirements.getRange(`E4:E${3 + requirementRows.length}`).conditionalFormats.add(
  "containsText",
  { text: "MISSING", format: { fill: lightRed, font: { color: red, bold: true } } },
);
requirements.freezePanes.freezeRows(3);

// Open items
title(openItems, "A1:G1", "Open Deviations, Risks and Requirement Gaps");
openItems.getRange("A3:G3").values = [[
  "ID",
  "Severity",
  "Type",
  "Finding",
  "Impact",
  "Required Action",
  "State",
]];
header(openItems.getRange("A3:G3"));
openItems.getRange("A4:G8").values = [
  ["DEV-BMS-LINK-001", "P0", "Requirement/Product", "1000 ms link timeout may receive extra 3-sample confirmation.", "Late isolation and requirement mismatch.", "Measure on HIL; fix implementation or approve requirement change.", "OPEN"],
  ["DEV-EVSE-LAYOUT-001", "P0", "Configuration", "EVSE linker FLASH region ends at 0x08200000; staging starts at 0x08100000.", "OTA staging can overlap application.", "Limit app linker region to 896 KiB and gate BIN/vector.", "OPEN"],
  ["DEV-OTA-GAP-001", "P0", "Requirement Gap", "No approved version, rollback or signed target-binding contract.", "Downgrade/wrong-target/power-loss safety cannot be claimed.", "Approve SWRS-OTA-007..009 and implement recovery/security.", "GAP"],
  ["DEV-GA-CONTRACT-001", "P2", "Contract", "Gateway schema and source boundary are not approved.", "Gateway expected results would be invented.", "Approve ICD before executable functional testing.", "BLOCKED"],
  ["DEV-SEC-001", "P0", "Security", "EVSE source configuration contains plaintext credential material.", "Credential disclosure and uncontrolled reuse.", "Rotate/remove secret and add secret scanning; never copy value into evidence.", "OPEN"],
];
const openTable = openItems.tables.add("A3:G8", true, "OpenItemsTable");
openTable.style = "TableStyleMedium4";
openItems.getRange("A4:G8").format = { wrapText: true, verticalAlignment: "top", rowHeight: 48 };
openItems.getRange("A:A").format.columnWidth = 25;
openItems.getRange("B:C").format.columnWidth = 18;
openItems.getRange("D:F").format.columnWidth = 42;
openItems.getRange("G:G").format.columnWidth = 15;
openItems.getRange("G4:G8").conditionalFormats.add("containsText", {
  text: "OPEN",
  format: { fill: lightRed, font: { color: red, bold: true } },
});
openItems.getRange("G4:G8").conditionalFormats.add("containsText", {
  text: "GAP",
  format: { fill: lightAmber, font: { color: "#7C2D12", bold: true } },
});
openItems.freezePanes.freezeRows(3);

// Legend
title(legend, "A1:D1", "Result Classification and Evidence Rules");
legend.getRange("A3:D3").values = [["Classification", "Meaning", "Owner", "PASS impact"]];
header(legend.getRange("A3:D3"));
legend.getRange("A4:D11").values = [
  ["NOT_EXECUTED", "Test has not run against the controlled baseline.", "QA", "No claim"],
  ["PASS", "Observed result meets the independent oracle with complete evidence.", "QA", "Qualifying"],
  ["FAIL_PRODUCT", "Controlled product differs from approved requirement.", "Development", "Blocks affected scope"],
  ["GAP_REQUIREMENT", "Requirement/mechanism is absent or unapproved.", "Requirement owner", "Blocks claim"],
  ["FAIL_TEST", "Automation/oracle/test setup is defective.", "QA automation", "No product verdict"],
  ["BLOCKED_INFRA", "Fixture, adapter, access or precondition is unavailable.", "HIL/DevOps", "No product verdict"],
  ["MISMATCH_CONFIGURATION", "SHA, board, build option or memory layout is not the baseline.", "CM/QA", "No product verdict"],
  ["NOT_APPLICABLE", "Approved scope excludes the test for this baseline.", "Requirement owner", "Document rationale"],
];
legend.getRange("A13:D13").values = [["Mandatory evidence", "Why", "Example", "Rule"]];
header(legend.getRange("A13:D13"));
legend.getRange("A14:D18").values = [
  ["Product full SHA", "Identifies source exactly", "40 hex", "Required"],
  ["ELF/BIN SHA-256", "Binds build output", "64 hex", "Required"],
  ["OpenOCD verify_image + IDCODE", "Binds artifact to target", "raw verify output", "Required for HIL"],
  ["Independent oracle", "Avoids product self-confirmation", "GPIO/fixture/QA calculation", "Required"],
  ["Raw timestamps/logs", "Supports timing and sequence", "JSONL/CAN trace", "Required when relevant"],
];
legend.getRange("A4:D18").format = { wrapText: true, verticalAlignment: "top" };
legend.getRange("A:A").format.columnWidth = 28;
legend.getRange("B:B").format.columnWidth = 54;
legend.getRange("C:D").format.columnWidth = 28;
legend.freezePanes.freezeRows(3);

// Inspect high-impact regions and scan formula/value errors before export.
const summaryInspect = await workbook.inspect({
  kind: "region",
  sheetId: "Summary",
  range: "A1:K18",
  maxChars: 6000,
});
const rtmInspect = await workbook.inspect({
  kind: "region",
  sheetId: "RTM",
  range: "A1:O10",
  maxChars: 6000,
});
console.log(summaryInspect.ndjson);
console.log(rtmInspect.ndjson);

const errorTokens = ["#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A"];
for (const sheet of [summary, rtm, requirements, openItems, legend, traceMap]) {
  const used = sheet.getUsedRange();
  const values = used.values.flat();
  const errors = values.filter((value) =>
    typeof value === "string" && errorTokens.some((token) => value.includes(token)),
  );
  if (errors.length) {
    throw new Error(`${sheet.name} contains formula errors: ${errors.join(", ")}`);
  }
  const preview = await workbook.render({
    sheetName: sheet.name,
    autoCrop: "all",
    scale: sheet.name === "RTM" ? 0.55 : 0.8,
    format: "png",
  });
  await fs.writeFile(
    path.join(outputDir, `${sheet.name}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(outputDir, "RTM.xlsx"));
console.log(path.join(outputDir, "RTM.xlsx"));
