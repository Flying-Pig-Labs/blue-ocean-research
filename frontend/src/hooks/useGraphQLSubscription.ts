import { useState, useEffect, useRef } from 'react';

interface GraphQLSubscriptionConfig {
  url: string;
  apiKey: string;
  region?: string;
}

interface GraphQLSubscriptionResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'reconnecting';
}

interface GraphQLMessage {
  id: string;
  type: string;
  payload?: any;
}

// Environment variables or config
const GRAPHQL_CONFIG: GraphQLSubscriptionConfig = {
  url: process.env.REACT_APP_GRAPHQL_URL || '',
  apiKey: process.env.REACT_APP_GRAPHQL_API_KEY || '',
  region: process.env.REACT_APP_AWS_REGION || 'us-east-1',
};

/**
 * Custom hook for GraphQL subscriptions over WebSocket
 */
export function useGraphQLSubscription<T>(
  subscription: string,
  variables?: Record<string, any>
): GraphQLSubscriptionResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [connectionState, setConnectionState] = useState<'disconnected' | 'connecting' | 'connected' | 'reconnecting'>('disconnected');
  
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const subscriptionIdRef = useRef<string | null>(null);
  const reconnectAttemptsRef = useRef(0);
  
  const maxReconnectAttempts = 10;
  const baseReconnectDelay = 1000; // 1 second

  const connect = () => {
    if (!GRAPHQL_CONFIG.url || !GRAPHQL_CONFIG.apiKey) {
      setError(new Error('GraphQL configuration is missing'));
      setLoading(false);
      return;
    }

    setConnectionState('connecting');
    setError(null);

    // Create WebSocket URL with authentication
    const wsUrl = GRAPHQL_CONFIG.url
      .replace('https://', 'wss://')
      .replace('http://', 'ws/')
      .replace('/graphql', '/graphql/realtime');
    
    const authUrl = `${wsUrl}?header=${btoa(JSON.stringify({
      host: new URL(GRAPHQL_CONFIG.url).hostname,
      'x-api-key': GRAPHQL_CONFIG.apiKey,
    }))}`;

    websocketRef.current = new WebSocket(authUrl, ['graphql-ws']);

    websocketRef.current.onopen = () => {
      console.log('WebSocket connected');
      setConnectionState('connected');
      setError(null);
      reconnectAttemptsRef.current = 0;

      // Send connection init
      sendMessage({
        type: 'connection_init',
      });
    };

    websocketRef.current.onmessage = (event) => {
      const message: GraphQLMessage = JSON.parse(event.data);
      
      switch (message.type) {
        case 'connection_ack':
          console.log('Connection acknowledged');
          // Start subscription
          startSubscription();
          break;
          
        case 'connection_error':
          console.error('Connection error:', message.payload);
          setError(new Error(message.payload?.message || 'Connection error'));
          break;
          
        case 'data':
          if (message.payload?.data) {
            setData(message.payload.data);
            setLoading(false);
          }
          if (message.payload?.errors) {
            setError(new Error(message.payload.errors[0]?.message || 'GraphQL error'));
          }
          break;
          
        case 'error':
          console.error('Subscription error:', message.payload);
          setError(new Error(message.payload?.message || 'Subscription error'));
          break;
          
        case 'complete':
          console.log('Subscription completed');
          setLoading(false);
          break;
          
        default:
          console.log('Unknown message type:', message.type);
      }
    };

    websocketRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError(new Error('WebSocket connection error'));
    };

    websocketRef.current.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      setConnectionState('disconnected');
      
      // Attempt to reconnect if not manually closed
      if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
        scheduleReconnect();
      } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
        setError(new Error('Max reconnection attempts reached'));
        setLoading(false);
      }
    };
  };

  const scheduleReconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    const delay = baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current);
    console.log(`Scheduling reconnect in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1})`);
    
    setConnectionState('reconnecting');
    reconnectAttemptsRef.current += 1;

    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, delay);
  };

  const sendMessage = (message: Omit<GraphQLMessage, 'id'>) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      const messageWithId = {
        id: subscriptionIdRef.current || generateId(),
        ...message,
      };
      websocketRef.current.send(JSON.stringify(messageWithId));
    }
  };

  const startSubscription = () => {
    subscriptionIdRef.current = generateId();
    
    sendMessage({
      type: 'start',
      payload: {
        query: subscription,
        variables: variables || {},
      },
    });
    
    setLoading(true);
  };

  const stopSubscription = () => {
    if (subscriptionIdRef.current) {
      sendMessage({
        type: 'stop',
      });
      subscriptionIdRef.current = null;
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    stopSubscription();
    
    if (websocketRef.current) {
      websocketRef.current.close(1000, 'Manual disconnect');
      websocketRef.current = null;
    }
    
    setConnectionState('disconnected');
    reconnectAttemptsRef.current = 0;
  };

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [subscription, JSON.stringify(variables)]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, []);

  return {
    data,
    loading,
    error,
    connectionState,
  };
}

/**
 * Hook for making GraphQL queries/mutations (non-subscription)
 */
export function useGraphQLQuery<T>(
  query: string,
  variables?: Record<string, any>
): GraphQLSubscriptionResult<T> & { refetch: () => Promise<void> } {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const executeQuery = async () => {
    if (!GRAPHQL_CONFIG.url || !GRAPHQL_CONFIG.apiKey) {
      setError(new Error('GraphQL configuration is missing'));
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(GRAPHQL_CONFIG.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': GRAPHQL_CONFIG.apiKey,
        },
        body: JSON.stringify({
          query,
          variables: variables || {},
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.errors) {
        throw new Error(result.errors[0]?.message || 'GraphQL error');
      }

      setData(result.data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    executeQuery();
  }, [query, JSON.stringify(variables)]);

  return {
    data,
    loading,
    error,
    connectionState: 'connected', // Not applicable for queries
    refetch: executeQuery,
  };
}

/**
 * Hook for GraphQL mutations
 */
export function useGraphQLMutation<T>() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const executeMutation = async (
    mutation: string,
    variables?: Record<string, any>
  ): Promise<T> => {
    if (!GRAPHQL_CONFIG.url || !GRAPHQL_CONFIG.apiKey) {
      throw new Error('GraphQL configuration is missing');
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(GRAPHQL_CONFIG.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': GRAPHQL_CONFIG.apiKey,
        },
        body: JSON.stringify({
          query: mutation,
          variables: variables || {},
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.errors) {
        throw new Error(result.errors[0]?.message || 'GraphQL error');
      }

      return result.data;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return {
    executeMutation,
    loading,
    error,
  };
}

// Utility function to generate unique IDs
function generateId(): string {
  return Math.random().toString(36).substr(2, 9);
}