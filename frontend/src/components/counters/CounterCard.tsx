'use client';

import { useState, useEffect } from 'react';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { counterAPI } from '@/lib/api';
import { PlusIcon, MinusIcon } from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';

interface CounterCardProps {
  title: string;
  count: number;
  todayCount: number;
  type: 'sit' | 'ticket';
}

export function CounterCard({ title, count: initialCount, todayCount, type }: CounterCardProps) {
  const [count, setCount] = useState(initialCount);
  const [isUpdating, setIsUpdating] = useState(false);
  const { sendCounterUpdate, onCounterUpdate } = useWebSocket();

  useEffect(() => {
    setCount(initialCount);
  }, [initialCount]);

  useEffect(() => {
    const unsubscribe = onCounterUpdate((data) => {
      if (data.counter_type === type) {
        setCount(data.count);
      }
    });

    return unsubscribe;
  }, [type, onCounterUpdate]);

  const handleUpdate = async (action: 'increment' | 'decrement') => {
    if (isUpdating) return;
    
    setIsUpdating(true);
    
    try {
      // Send via WebSocket for real-time update
      // The WebSocket callback will handle the state update
      sendCounterUpdate(type, action, 1);
    } catch (error) {
      toast.error('Failed to update counter');
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="bg-dark-card rounded-lg p-6 border border-dark-border">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <span className="text-sm text-gray-400">Today: {todayCount}</span>
      </div>
      
      <div className="flex items-center justify-center gap-6">
        <button
          onClick={() => handleUpdate('decrement')}
          disabled={isUpdating || count === 0}
          className="counter-btn counter-btn-remove"
        >
          <MinusIcon className="w-6 h-6" />
        </button>
        
        <div className="text-center">
          <span className="text-5xl font-bold text-white">{count}</span>
          <p className="text-sm text-gray-400 mt-1">Total {title}</p>
        </div>
        
        <button
          onClick={() => handleUpdate('increment')}
          disabled={isUpdating}
          className="counter-btn counter-btn-add"
        >
          <PlusIcon className="w-6 h-6" />
        </button>
      </div>
    </div>
  );
}
