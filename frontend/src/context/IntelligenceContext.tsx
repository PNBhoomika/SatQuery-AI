import React, { createContext, useContext, useState, useEffect } from 'react';
import { SearchResult, SearchResponse, Alert, Cluster, ChangeAnalysis, FeedbackPayload, SystemHealth } from '../types/api';
import { apiService } from '../services/api';

interface IntelligenceContextType {
  activeQuery: string;
  setActiveQuery: (q: string) => void;
  searchResults: SearchResult[];
  isSearching: boolean;
  searchError: string | null;
  /** 'AVAILABLE' | 'UNAVAILABLE' | null — null means no search has been run yet */
  searchCoverage: 'AVAILABLE' | 'UNAVAILABLE' | null;
  /** Human-readable message about the search result / coverage status */
  searchMessage: string | null;
  /** List of indexable AOIs to suggest when coverage is UNAVAILABLE */
  searchAvailableAois: string[];
  /** The parsed query metadata from the backend (location, change_types, years) */
  searchParsedQuery: SearchResponse['parsed_query'] | null;
  executeSearch: (query: string) => Promise<void>;
  executeImageSearch: (file: File) => Promise<void>;
  selectedResult: SearchResult | null;
  setSelectedResult: (res: SearchResult | null) => void;
  alerts: Alert[];
  clusters: Cluster[];
  selectedCluster: Cluster | null;
  setSelectedCluster: (c: Cluster | null) => void;
  selectedAlert: Alert | null;
  setSelectedAlert: (a: Alert | null) => void;
  feedbackModalAlert: Alert | null;
  setFeedbackModalAlert: (a: Alert | null) => void;
  submitFeedback: (payload: FeedbackPayload) => Promise<boolean>;
  mapCenter: [number, number];
  setMapCenter: (coords: [number, number]) => void;
  mapZoom: number;
  setMapZoom: (z: number) => void;
  systemHealth: SystemHealth | null;
  isDemoActive: boolean;
  launchDemoScenario: () => Promise<void>;
  refreshAlerts: () => Promise<void>;
}

const IntelligenceContext = createContext<IntelligenceContextType | undefined>(undefined);

export const IntelligenceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeQuery, setActiveQuery] = useState('Find large construction areas and solar arrays near rivers');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchCoverage, setSearchCoverage] = useState<'AVAILABLE' | 'UNAVAILABLE' | null>(null);
  const [searchMessage, setSearchMessage] = useState<string | null>(null);
  const [searchAvailableAois, setSearchAvailableAois] = useState<string[]>([]);
  const [searchParsedQuery, setSearchParsedQuery] = useState<SearchResponse['parsed_query'] | null>(null);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [selectedCluster, setSelectedCluster] = useState<Cluster | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [feedbackModalAlert, setFeedbackModalAlert] = useState<Alert | null>(null);

  const [mapCenter, setMapCenter] = useState<[number, number]>([13.3408, 77.1009]);
  const [mapZoom, setMapZoom] = useState<number>(12);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [isDemoActive, setIsDemoActive] = useState(false);

  // Initial load
  useEffect(() => {
    loadInitialIntelligence();
  }, []);

  const loadInitialIntelligence = async () => {
    try {
      const [alertsData, clustersData, healthData, searchResp] = await Promise.all([
        apiService.getAlerts(),
        apiService.getClusters(),
        apiService.getHealth(),
        apiService.searchSemantic('Tumakuru industrial and solar development'),
      ]);
      setAlerts(alertsData);
      setClusters(clustersData);
      setSystemHealth(healthData);
      setSearchCoverage(searchResp.coverage);
      setSearchMessage(searchResp.message);
      setSearchAvailableAois(searchResp.available_aois || []);
      setSearchParsedQuery(searchResp.parsed_query || null);
      setSearchResults(searchResp.results);
      if (searchResp.results.length > 0) {
        setSelectedResult(searchResp.results[0]);
      }
      if (alertsData.length > 0) {
        setSelectedAlert(alertsData[0]);
      }
    } catch (err) {
      console.error('Error loading intelligence data', err);
    }
  };

  const executeSearch = async (query: string) => {
    setIsSearching(true);
    setSearchError(null);
    setActiveQuery(query);
    try {
      const resp = await apiService.searchSemantic(query);
      setSearchCoverage(resp.coverage);
      setSearchMessage(resp.message);
      setSearchAvailableAois(resp.available_aois || []);
      setSearchParsedQuery(resp.parsed_query || null);
      setSearchResults(resp.results);
      if (resp.results.length > 0) {
        setSelectedResult(resp.results[0]);
        setMapCenter([resp.results[0].latitude, resp.results[0].longitude]);
        setMapZoom(13);
      } else {
        // UNAVAILABLE or empty — keep map where it is, clear selection
        setSelectedResult(null);
      }
    } catch (err: any) {
      setSearchError('Unable to retrieve intelligence data. Please retry.');
    } finally {
      setIsSearching(false);
    }
  };

  const executeImageSearch = async (file: File) => {
    setIsSearching(true);
    setSearchError(null);
    try {
      const results = await apiService.searchByImage(file);
      setSearchCoverage('AVAILABLE');
      setSearchMessage(`Retrieved ${results.length} visually similar satellite tiles.`);
      setSearchAvailableAois([]);
      setSearchParsedQuery(null);
      setSearchResults(results);
      if (results.length > 0) {
        setSelectedResult(results[0]);
        setMapCenter([results[0].latitude, results[0].longitude]);
      }
    } catch (err) {
      setSearchError('Error processing image tile embedding.');
    } finally {
      setIsSearching(false);
    }
  };

  const submitFeedback = async (payload: FeedbackPayload): Promise<boolean> => {
    const success = await apiService.submitFeedback(payload);
    if (success) {
      // Refresh alerts list locally
      const updated = await apiService.getAlerts();
      setAlerts(updated);
      if (selectedAlert && selectedAlert.id === payload.alert_id) {
        setSelectedAlert({
          ...selectedAlert,
          status: payload.action === 'CONFIRM' ? 'CONFIRMED' : 'REJECTED',
        });
      }
    }
    return success;
  };

  const refreshAlerts = async () => {
    const data = await apiService.getAlerts();
    setAlerts(data);
  };

  const launchDemoScenario = async () => {
    setIsDemoActive(true);
    const tumakuruCoords: [number, number] = [13.3408, 77.1009];
    setMapCenter(tumakuruCoords);
    setMapZoom(13);
    const resp = await apiService.searchSemantic('Tumakuru high-tech industrial & solar corridor');
    setSearchCoverage(resp.coverage);
    setSearchMessage(resp.message);
    setSearchAvailableAois(resp.available_aois || []);
    setSearchParsedQuery(resp.parsed_query || null);
    setSearchResults(resp.results);
    if (resp.results.length > 0) {
      setSelectedResult(resp.results[0]);
    }
    const matchingAlert = alerts.find(a => a.id === 'ALT-2026-024') || alerts[0];
    if (matchingAlert) {
      setSelectedAlert(matchingAlert);
    }
  };

  return (
    <IntelligenceContext.Provider
      value={{
        activeQuery,
        setActiveQuery,
        searchResults,
        isSearching,
        searchError,
        searchCoverage,
        searchMessage,
        searchAvailableAois,
        searchParsedQuery,
        executeSearch,
        executeImageSearch,
        selectedResult,
        setSelectedResult,
        alerts,
        clusters,
        selectedCluster,
        setSelectedCluster,
        selectedAlert,
        setSelectedAlert,
        feedbackModalAlert,
        setFeedbackModalAlert,
        submitFeedback,
        mapCenter,
        setMapCenter,
        mapZoom,
        setMapZoom,
        systemHealth,
        isDemoActive,
        launchDemoScenario,
        refreshAlerts,
      }}
    >
      {children}
    </IntelligenceContext.Provider>
  );
};

export const useIntelligence = () => {
  const context = useContext(IntelligenceContext);
  if (!context) {
    throw new Error('useIntelligence must be used within an IntelligenceProvider');
  }
  return context;
};
