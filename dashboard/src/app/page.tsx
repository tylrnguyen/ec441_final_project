import { promises as fs } from "fs";
import path from "path";
import NetStressDashboard from "./dashboard";

export default async function Page() {
  const filePath = path.join(process.cwd(), "public", "dashboard_data.json");
  const raw = await fs.readFile(filePath, "utf-8");
  const data = JSON.parse(raw);
  return <NetStressDashboard initialData={data} />;
}
