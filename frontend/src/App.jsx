import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ReactFlow, Controls, Background, applyNodeChanges, applyEdgeChanges, MarkerType } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Send, TerminalSquare, Loader2, Workflow, MessageSquare, Wrench, Plus, History, Clock, Edit2, Check, X } from 'lucide-react';
import CustomNode from './CustomNode';
import './index.css';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

const initialNodes = [
  { id: '__start__', type: 'customNode', position: { x: 50, y: 200 }, data: { label: 'Trigger', icon: 'start', sublabel: 'Awaiting Prompt' } }
];

const initialEdges = [];

const nodeTypes = { customNode: CustomNode };

function App() {
  const [nodes, setNodes] = useState(initialNodes);
  const [edges, setEdges] = useState(initialEdges);
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [chatOpen, setChatOpen] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [historyLogs, setHistoryLogs] = useState([]);
  const [viewingHistoryId, setViewingHistoryId] = useState(null);
  
  const [workflowName, setWorkflowName] = useState('AgentX Workflow');
  const [isEditingName, setIsEditingName] = useState(false);
  const [tempName, setTempName] = useState('');

  // Fetch history on mount
  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/history`);
      if (res.ok) {
        const data = await res.json();
        setHistoryLogs(data);
      }
    } catch (e) { console.error('Error fetching history', e); }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const loadHistoryRun = async (id) => {
    try {
      const res = await fetch(`${API_BASE_URL}/history/${id}`);
      if (res.ok) {
        const data = await res.json();
        setViewingHistoryId(id);
        
        // Rebuild layout correctly
        let currentX = 50;
        let lastNodeId = '__start__';
        const rebuiltNodes = [
          { id: '__start__', type: 'customNode', position: { x: currentX, y: 200 }, data: { label: 'Trigger', icon: 'start', sublabel: data.prompt, isActive: false } }
        ];
        const rebuiltEdges = [];
        
        const toolsCalled = data.graph_data?.executed_tools || [];
        
        toolsCalled.forEach((tc, idx) => {
           currentX += 300;
           const newNodeId = `tool-hist-${idx}`;
           rebuiltNodes.push({ id: newNodeId, type: 'customNode', position: { x: currentX, y: 200 }, data: { label: tc.name, icon: 'tools', sublabel: 'Executed API', isActive: false } });
           rebuiltEdges.push({
             id: `e-${lastNodeId}-${newNodeId}`, source: lastNodeId, target: newNodeId, animated: false, style: { strokeWidth: 2, stroke: '#b3b3b3' }, markerEnd: { type: MarkerType.ArrowClosed }
           });
           lastNodeId = newNodeId;
        });

        // Add End node
        currentX += 300;
        const endNodeId = '__end__';
        rebuiltNodes.push({ id: endNodeId, type: 'customNode', position: { x: currentX, y: 200 }, data: { label: 'Complete', icon: 'end', sublabel: 'Workflow finished', isActive: false } });
        rebuiltEdges.push({
          id: `e-${lastNodeId}-${endNodeId}`, source: lastNodeId, target: endNodeId, animated: false, style: { strokeWidth: 2, stroke: '#b3b3b3' }, markerEnd: { type: MarkerType.ArrowClosed }
        });

        setNodes(rebuiltNodes);
        setEdges(rebuiltEdges);
        setMessages(data.messages || []);
        setPrompt(data.prompt);
        setWorkflowName(data.name || 'Untitled Workflow');
      }
    } catch (e) {
      console.error(e);
    }
  };

  const createNewWorkflow = () => {
    setViewingHistoryId(null);
    setNodes(initialNodes);
    setEdges(initialEdges);
    setMessages([]);
    setPrompt('');
    setWorkflowName('AgentX Workflow');
  };

  const handleSaveName = async () => {
    if (tempName.trim()) {
      setWorkflowName(tempName);
      if (viewingHistoryId) {
        try {
          await fetch(`${API_BASE_URL}/history/${viewingHistoryId}/name`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: tempName })
          });
          fetchHistory(); // Refresh sidebar list
        } catch (e) {
          console.error('Failed to update name', e);
        }
      }
    }
    setIsEditingName(false);
  };

  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  const onEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const setActiveNode = (nodeId) => {
    setNodes((nds) =>
      nds.map((n) => {
        n.data = { ...n.data, isActive: n.id === nodeId };
        return n;
      })
    );
  };

  const handleRun = async (e) => {
    e.preventDefault();
    if (!prompt.trim() || isRunning) return;

    setIsRunning(true);
    setChatOpen(true);
    setMessages(prev => [...prev, { role: 'user', content: prompt }]);
    const currentPrompt = prompt;
    setPrompt('');

    // Reset DAG for this run
    let currentX = 50;
    let lastNodeId = '__start__';
    
    setNodes([{ id: '__start__', type: 'customNode', position: { x: currentX, y: 200 }, data: { label: 'Trigger', icon: 'start', sublabel: currentPrompt, isActive: true } }]);
    setEdges([]);

    try {
      const response = await fetch(`${API_BASE_URL}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: currentPrompt })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6).trim();
            if (!dataStr) continue;
            
            try {
              const data = JSON.parse(dataStr);
              if (data.done) {
                // Add final end node
                currentX += 300;
                const endNodeId = '__end__';
                setNodes(prev => [
                  ...prev.map(n => ({...n, data: {...n.data, isActive: false}})),
                  { id: endNodeId, type: 'customNode', position: { x: currentX, y: 200 }, data: { label: 'Complete', icon: 'end', sublabel: 'Workflow finished', isActive: true } }
                ]);
                setEdges(prev => [...prev.map(e => ({...e, animated: false})), {
                  id: `e-${lastNodeId}-${endNodeId}`, source: lastNodeId, target: endNodeId, animated: false, style: { strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed }
                }]);
                break;
              }
              if (data.error) {
                setMessages(prev => [...prev, { role: 'error', content: data.error }]);
                continue;
              }

              if (data.tool_calls && data.tool_calls.length > 0) {
                // Create a node for each tool call in the workflow DAG
                data.tool_calls.forEach((tc, idx) => {
                  currentX += 300;
                  const newNodeId = `tool-${tc.id || Date.now()}-${idx}`;
                  
                  setNodes(prev => [
                    ...prev.map(n => ({...n, data: {...n.data, isActive: false}})),
                    { id: newNodeId, type: 'customNode', position: { x: currentX, y: 200 }, data: { label: tc.name, icon: 'tools', sublabel: 'Executing API...', isActive: true } }
                  ]);
                  
                  setEdges(prev => [...prev.map(e => ({...e, animated: false})), {
                    id: `e-${lastNodeId}-${newNodeId}`,
                    source: lastNodeId,
                    target: newNodeId,
                    animated: true,
                    style: { stroke: '#FF6E4A', strokeWidth: 3 },
                    markerEnd: { type: MarkerType.ArrowClosed }
                  }]);
                  
                  lastNodeId = newNodeId;
                });
              }

              if (data.content || (data.tool_calls && data.tool_calls.length > 0)) {
                setMessages(prev => [...prev, {
                  role: data.type === 'ai' ? 'assistant' : data.node,
                  content: data.content,
                  tool_calls: data.tool_calls,
                  node: data.node
                }]);
              }
            } catch (err) {
              console.error('Failed to parse SSE data', err, dataStr);
            }
          }
        }
      }
    } catch (err) {
      console.error('Run failed', err);
      setMessages(prev => [...prev, { role: 'error', content: `Run failed: ${err.message}` }]);
    } finally {
      setIsRunning(false);
      setTimeout(() => {
        setNodes(nds => nds.map(n => ({...n, data: {...n.data, isActive: false}})));
        setEdges(eds => eds.map(e => ({...e, animated: false, style: {strokeWidth: 2}})));
        fetchHistory(); // Refresh history list after run
      }, 1500);
    }
  };

  return (
    <div className="h-screen w-full flex overflow-hidden bg-[#fafafa]">
      
      {/* Sidebar - N8N style dark sidebar */}
      <aside className={`${sidebarOpen ? 'w-[280px]' : 'w-[60px]'} bg-[#2B2B35] flex flex-col items-center py-4 text-gray-400 z-20 shadow-xl border-r border-[#1a1a24] transition-all overflow-hidden`}>
        <div className="w-10 h-10 min-h-10 bg-[#FF6E4A] rounded-xl flex flex-shrink-0 items-center justify-center text-white mb-6 mt-1 cursor-pointer" onClick={() => setSidebarOpen(!sidebarOpen)}>
          <Workflow />
        </div>
        
        <div className="flex flex-col w-full px-3 gap-2">
           <button onClick={createNewWorkflow} className={`flex items-center gap-3 p-2.5 rounded-lg transition-colors hover:bg-white/5 hover:text-white ${!viewingHistoryId ? 'bg-[#FF6E4A]/10 text-[#FF6E4A] hover:bg-[#FF6E4A]/20' : ''}`} title="New Workflow">
             <Plus size={22} className="flex-shrink-0" />
             {sidebarOpen && <span className="font-semibold text-[14px]">New Workflow</span>}
           </button>
           
           <button onClick={() => setSidebarOpen(!sidebarOpen)} className="flex items-center gap-3 p-2.5 rounded-lg transition-colors hover:bg-white/5 hover:text-white" title="Execution History">
             <History size={22} className="flex-shrink-0" />
             {sidebarOpen && <span className="font-medium text-[14px]">Executions</span>}
           </button>

           <div className="h-[1px] w-full bg-white/10 my-2"></div>

           {sidebarOpen && (
             <div className="flex flex-col gap-1 overflow-y-auto w-full custom-scroll" style={{maxHeight: 'calc(100vh - 200px)'}}>
               {historyLogs.map((log) => (
                 <div 
                   key={log.id} 
                   onClick={() => loadHistoryRun(log.id)}
                   className={`p-3 rounded-lg flex flex-col gap-1 cursor-pointer hover:bg-white/5 transition-colors ${viewingHistoryId === log.id ? 'bg-white/10 text-white' : ''}`}
                 >
                   <span className="text-[13px] font-medium truncate w-full" title={log.name || log.prompt}>{log.name || `"${log.prompt}"`}</span>
                   <span className="text-[11px] text-gray-500 flex items-center gap-1"><Clock size={10} /> {new Date(log.created_at).toLocaleString()}</span>
                 </div>
               ))}
               {historyLogs.length === 0 && <span className="text-xs text-center mt-4 text-gray-500">No logs yet</span>}
             </div>
           )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 relative flex">
        
        {/* XYFlow Editor Area */}
        <div className="flex-1 relative">
          <div className="absolute top-4 left-6 z-10">
             {isEditingName ? (
               <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-lg shadow-sm border border-[#FF6E4A]">
                 <input 
                   autoFocus
                   type="text" 
                   value={tempName} 
                   onChange={(e) => setTempName(e.target.value)}
                   onKeyDown={(e) => e.key === 'Enter' && handleSaveName()}
                   className="outline-none text-xl font-bold text-gray-800 bg-transparent w-[200px]"
                 />
                 <button onClick={handleSaveName} className="text-green-600 hover:bg-green-50 p-1 rounded"><Check size={18} /></button>
                 <button onClick={() => setIsEditingName(false)} className="text-gray-400 hover:bg-gray-100 p-1 rounded"><X size={18} /></button>
               </div>
             ) : (
               <div className="group flex items-center gap-2 cursor-pointer" onClick={() => { setTempName(workflowName); setIsEditingName(true); }}>
                 <h1 className="text-xl font-bold text-gray-800 tracking-tight flex flex-col">
                   {workflowName}
                   <span className="text-xs font-normal text-gray-500 mt-1">AI-Powered Interaction Graph</span>
                 </h1>
                 <div className="opacity-0 group-hover:opacity-100 p-1.5 text-gray-400 hover:text-[#FF6E4A] hover:bg-gray-200/50 rounded-md transition-all">
                   <Edit2 size={16} />
                 </div>
               </div>
             )}
          </div>
          
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            className="bg-[#fafbfc]"
            panOnScroll
            selectionOnDrag
          >
            <Background color="#efefef" gap={16} />
            <Controls className="!bg-white !shadow-md !border-gray-200" />
          </ReactFlow>
        </div>

        {/* Executions / Chat Panel */}
        {chatOpen && (
          <div className="w-[420px] bg-white border-l border-gray-200 flex flex-col shadow-2xl z-10 absolute right-0 top-0 bottom-0 animate-in slide-in-from-right-10">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 bg-white">
              <h2 className="text-[15px] font-semibold flex items-center gap-2 text-gray-800">
                <TerminalSquare className="w-4 h-4 text-[#FF6E4A]" />
                Execution Interactor
              </h2>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 bg-[#f8f9fa] custom-scroll">
              {messages.length === 0 && (
                <div className="text-center text-gray-400 mt-10 text-[13px] flex flex-col items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center">
                    <MessageSquare size={20} />
                  </div>
                  Type a prompt below to initiate <br/> the langgraph agent execution.
                </div>
              )}
              
              {messages.map((msg, i) => (
                <div key={i} className={`flex flex-col max-w-[90%] ${msg.role === 'user' ? 'self-end' : 'self-start'}`}>
                  <span className="text-[11px] mb-1 font-semibold text-gray-500 uppercase tracking-wider pl-1">
                    {msg.role === 'user' ? 'You' : msg.node === 'agent' ? 'Agent' : `Tool: ${msg.node}`}
                  </span>
                  <div className={`
                    p-3.5 rounded-2xl text-[14px] leading-relaxed relative shadow-sm
                    ${msg.role === 'user' 
                      ? 'bg-[#2B2B35] text-white rounded-tr-sm' 
                      : msg.role === 'error' 
                        ? 'bg-red-50 text-red-700 border border-red-100 rounded-tl-sm' 
                        : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm'}
                  `}>
                    {msg.content}
                    
                    {msg.tool_calls && msg.tool_calls.map((tc, idx) => (
                      <div key={idx} className="mt-3 p-3 bg-gray-50/80 border border-gray-100 rounded-lg text-[12px] font-mono shadow-inner text-gray-600">
                        <div className="flex items-center gap-2 text-[#FF6E4A] font-semibold mb-1">
                          <Wrench className="w-3 h-3" />
                          {tc.name}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {isRunning && (
                <div className="flex items-center gap-2 text-[13px] text-gray-500 self-start ml-2 p-2 relative">
                   <div className="flex bg-white shadow-sm border border-gray-200 rounded-full px-4 py-2 items-center gap-2">
                     <Loader2 className="w-4 h-4 animate-spin text-[#FF6E4A]" />
                     Processing...
                   </div>
                </div>
              )}
            </div>
            
            {/* Input Footer */}
            <div className="p-4 bg-white border-t border-gray-100 shadow-[0_-4px_20px_-15px_rgba(0,0,0,0.1)]">
              <form onSubmit={handleRun} className="relative group">
                <input 
                  type="text" 
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Ask agent to perform a task..." 
                  className="w-full pl-4 pr-12 py-3.5 bg-gray-50 focus:bg-white border border-gray-200 focus:border-[#FF6E4A] focus:ring-4 focus:ring-[#FF6E4A]/10 rounded-xl outline-none text-[14px] transition-all disabled:opacity-50"
                  disabled={isRunning || viewingHistoryId}
                />
                <button 
                  type="submit" 
                  className={`
                    absolute right-2 top-2 bottom-2 aspect-square flex items-center justify-center rounded-lg transition-all
                    ${(isRunning || viewingHistoryId)
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                        : prompt.length > 0 
                            ? 'bg-[#FF6E4A] text-white hover:bg-[#E95C39] hover:shadow-md hover:scale-105 active:scale-95' 
                            : 'bg-gray-100 text-gray-400'}
                  `}
                  disabled={isRunning || !prompt.trim() || viewingHistoryId}
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
