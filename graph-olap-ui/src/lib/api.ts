import {
  type Mapping,
  type Instance,
  type InstanceProgress,
  mockMappings,
  mockInstances,
} from "./mock-data";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Mappings
// ---------------------------------------------------------------------------

export async function listMappings(): Promise<Mapping[]> {
  try {
    return await request<Mapping[]>("/api/mappings");
  } catch (err) {
    console.warn("Failed to fetch mappings, using mock data:", err);
    return mockMappings;
  }
}

export async function getMapping(id: string): Promise<Mapping> {
  try {
    return await request<Mapping>(`/api/mappings/${id}`);
  } catch (err) {
    console.warn("Failed to fetch mapping, using mock data:", err);
    const found = mockMappings.find((m) => m.id === id);
    if (!found) throw new Error(`Mapping ${id} not found`);
    return found;
  }
}

export async function createMapping(
  data: Omit<Mapping, "id" | "createdAt" | "updatedAt" | "version" | "owner">
): Promise<Mapping> {
  return request<Mapping>("/api/mappings", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateMapping(
  id: string,
  data: Partial<Mapping>
): Promise<Mapping> {
  return request<Mapping>(`/api/mappings/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteMapping(id: string): Promise<void> {
  await request<void>(`/api/mappings/${id}`, { method: "DELETE" });
}

// ---------------------------------------------------------------------------
// Instances
// ---------------------------------------------------------------------------

export async function listInstances(): Promise<Instance[]> {
  try {
    return await request<Instance[]>("/api/instances");
  } catch (err) {
    console.warn("Failed to fetch instances, using mock data:", err);
    return mockInstances;
  }
}

export async function getInstance(id: string): Promise<Instance> {
  try {
    return await request<Instance>(`/api/instances/${id}`);
  } catch (err) {
    console.warn("Failed to fetch instance, using mock data:", err);
    const found = mockInstances.find((i) => i.id === id);
    if (!found) throw new Error(`Instance ${id} not found`);
    return found;
  }
}

export async function createInstance(data: {
  name: string;
  mappingId: string;
  wrapperType: "falkordb" | "ryugraph";
  ttl: number;
  cpuCores: number;
}): Promise<Instance> {
  return request<Instance>("/api/instances", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function terminateInstance(id: string): Promise<void> {
  await request<void>(`/api/instances/${id}`, { method: "DELETE" });
}

export async function getInstanceProgress(
  id: string
): Promise<InstanceProgress> {
  return request<InstanceProgress>(`/api/instances/${id}/progress`);
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export async function healthCheck(): Promise<{ status: string }> {
  return request<{ status: string }>("/health");
}
