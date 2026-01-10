'use client';

import { useState, useEffect } from 'react';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { counterAPI, systemAPI } from '@/lib/api';
import { PlusIcon, MinusIcon } from '@heroicons/react/24/solid';
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface CounterCardProps {
  title: string;
  count: number;
  todayCount: number;
  type: 'sit' | 'ticket';
  quota?: number;
  weeklyCount?: number;
}

export function CounterCard({ title, count: initialCount, todayCount, type, quota, weeklyCount }: CounterCardProps) {
  const [count, setCount] = useState(initialCount);
  const [isUpdating, setIsUpdating] = useState(false);
  const { sendCounterUpdate, onCounterUpdate } = useWebSocket();
  
  const progress = quota && weeklyCount ? (weeklyCount / quota) * 100 : 0;
  const isComplete = quota && weeklyCount ? weeklyCount >= quota : false;
  const isNearComplete = quota && weeklyCount ? weeklyCount >= quota * 0.8 : false;

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
        <div className="flex flex-col items-end gap-1">
          <span className="text-sm text-gray-400">Today: {todayCount}</span>
          {quota && weeklyCount !== undefined && (
            <div className="flex items-center gap-1">
              {isComplete ? (
                <CheckCircleIcon className="w-4 h-4 text-green-500" />
              ) : isNearComplete ? (
                <ExclamationTriangleIcon className="w-4 h-4 text-yellow-500" />
              ) : null}
              <span className="text-xs text-gray-500">
                Week: {weeklyCount} / {quota}
              </span>
            </div>
          )}
        </div>
      </div>
      
      {/* Progress Bar */}
      {quota && weeklyCount !== undefined && (
        <div className="mb-4">
          <div className="w-full bg-gray-700 rounded-full h-2.5">
            <div
              className={`h-2.5 rounded-full transition-all duration-300 ${
                isComplete
                  ? 'bg-green-500'
                  : isNearComplete
                  ? 'bg-yellow-500'
                  : 'bg-primary-500'
              }`}
              style={{ width: `${Math.min(progress, 100)}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-400 mt-1 text-center">
            {isComplete
              ? '✓ Weekly quota completed!'
              : `${Math.round(progress)}% of weekly quota`}
          </p>
        </div>
      )}
      
      <div className="flex items-center justify-center gap-6">
        <button
          onClick={() => handleUpdate('decrement')}
          disabled={isUpdating || count === 0}
          className="counter-btn counter-btn-remove"
        >
          <MinusIcon className="w-6 h-6" />
        </button>
        
        <div className="text-center">
          <span className="text-5xl font-bold text-white">{weeklyCount ?? 0}</span>
          <p className="text-sm text-gray-400 mt-1">Total (This Week)</p>
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
