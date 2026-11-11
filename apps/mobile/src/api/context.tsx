import React, { createContext, useContext, useMemo, useState } from "react";
import { ConvoGlassesClient } from "./client";

interface ApiContextValue {
  client: ConvoGlassesClient;
  token: string;
  setToken: (token: string) => void;
  baseUrl: string;
  setBaseUrl: (url: string) => void;
}

const ApiContext = createContext<ApiContextValue | undefined>(undefined);

const DEFAULT_BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";
const DEFAULT_TOKEN = "dev-token-user-1";

export function ApiProvider({ children }: { children: React.ReactNode }) {
  const [baseUrl, setBaseUrl] = useState<string>(DEFAULT_BASE_URL);
  const [token, setToken] = useState<string>(DEFAULT_TOKEN);

  const client = useMemo(() => {
    return new ConvoGlassesClient({
      baseUrl,
      getAuthToken: () => token,
    });
  }, [baseUrl, token]);

  return (
    <ApiContext.Provider value={{ client, token, setToken, baseUrl, setBaseUrl }}>
      {children}
    </ApiContext.Provider>
  );
}

export function useApiClient(): ConvoGlassesClient {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error("useApiClient must be used within an ApiProvider");
  }
  return context.client;
}

export function useApiConfig() {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error("useApiConfig must be used within an ApiProvider");
  }
  return {
    token: context.token,
    setToken: context.setToken,
    baseUrl: context.baseUrl,
    setBaseUrl: context.setBaseUrl,
  };
}

