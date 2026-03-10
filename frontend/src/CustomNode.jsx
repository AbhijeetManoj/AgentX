import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { Play, BrainCircuit, Wrench, CheckCircle2 } from 'lucide-react';

const iconMap = {
  start: <Play className="w-5 h-5 text-emerald-500" />,
  agent: <BrainCircuit className="w-5 h-5 text-[#FF6E4A]" />,
  tools: <Wrench className="w-5 h-5 text-blue-500" />,
  end: <CheckCircle2 className="w-5 h-5 text-gray-500" />,
};

const CustomNode = ({ data, selected }) => {
  const isActive = data.isActive; // To highlight during run
  
  return (
    <div className={`
      relative min-w-[220px] bg-white rounded-xl border flex items-center shadow-sm 
      transition-all duration-300
      ${selected ? 'border-[#FF6E4A] ring-2 ring-[#FF6E4A]/20' : 'border-gray-200'}
      ${isActive ? 'ring-4 ring-[#FF6E4A]/40 shadow-xl scale-[1.02]' : 'hover:shadow-md hover:border-gray-300'}
    `}>
      {/* If it takes incoming connections (everything but start) */}
      {data.id !== '__start__' && (
        <Handle 
          type="target" 
          position={Position.Left} 
          className="w-3 h-3 bg-gray-400 border-2 border-white -ml-1.5"
        />
      )}

      {/* Node content: n8n style */}
      <div className="flex w-full overflow-hidden rounded-xl">
        <div className="w-[50px] flex items-center justify-center bg-gray-50 border-r border-gray-100 p-3">
          {iconMap[data.icon] || <BrainCircuit className="w-5 h-5 text-gray-500" />}
        </div>
        
        <div className="py-2 px-3 flex flex-col justify-center flex-1">
          <div className="text-[13px] font-semibold text-gray-800 leading-tight">
            {data.label}
          </div>
          {data.sublabel && (
            <div className="text-[11px] text-gray-500 mt-0.5 truncate max-w-[140px]">
              {data.sublabel}
            </div>
          )}
        </div>
        
        {/* Active pulsing dot */}
        {isActive && (
          <div className="absolute -top-1.5 -right-1.5 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FF6E4A] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-[#FF6E4A]"></span>
          </div>
        )}
      </div>

      {/* If it outputs (everything but end) */}
      {data.id !== '__end__' && (
        <Handle 
          type="source" 
          position={Position.Right} 
          className="w-3 h-3 bg-gray-400 border-2 border-white -mr-1.5"
        />
      )}
    </div>
  );
};

export default memo(CustomNode);
