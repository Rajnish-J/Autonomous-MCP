import React, { useState, useEffect } from 'react';
import { AlertCircle, Play, Camera, Globe, MousePointer, Type, MessageSquare, Monitor, Plus, Trash2, Clock } from 'lucide-react';

const PlaywrightController = () => {
  const [serverUrl] = useState('http://localhost:8000');
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [screenshotData, setScreenshotData] = useState(null);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState({ is_initialized: false, is_running: false });
  
  // User story form
  const [userStory, setUserStory] = useState('Login to website and take screenshot');
  const [steps, setSteps] = useState([
    { action: 'navigate', description: 'Go to login page', url: 'https://example.com/login' },
    { action: 'screenshot', description: 'Take initial screenshot' }
  ]);

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev.slice(-19), { message, type, timestamp }]);
  };

  const apiCall = async (endpoint, method = 'GET', data = null) => {
    try {
      const config = {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
      };
      
      if (data) {
        config.body = JSON.stringify(data);
      }
      
      const response = await fetch(`${serverUrl}${endpoint}`, config);
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Unknown error');
      }
      
      return result;
    } catch (err) {
      setError(err.message);
      addLog(`❌ ${err.message}`, 'error');
      throw err;
    }
  };

  const checkStatus = async () => {
    try {
      const response = await fetch(`${serverUrl}/status`);
      const result = await response.json();
      setStatus(result);
      return result;
    } catch (err) {
      setError('Server not reachable');
      addLog('❌ Server not reachable', 'error');
      return null;
    }
  };

  const fetchLogs = async () => {
    try {
      const result = await apiCall('/logs');
      if (result.data && result.data.logs) {
        setLogs(result.data.logs.map(log => ({
          message: log.message,
          type: log.level.toLowerCase(),
          timestamp: new Date(log.timestamp).toLocaleTimeString()
        })));
        setStatus(prev => ({
          ...prev,
          is_running: result.data.is_running,
          is_initialized: result.data.is_initialized
        }));
      }
    } catch (err) {
      // Ignore log fetch errors to avoid spam
    }
  };

  const handleRunPlaywright = async () => {
    if (!userStory.trim() || steps.length === 0) {
      addLog('Please enter a user story and add at least one step', 'error');
      return;
    }
    
    setIsRunning(true);
    setError(null);
    
    try {
      addLog(`🚀 Starting user story: ${userStory}`, 'info');
      const result = await apiCall('/run-playwright', 'POST', {
        user_story: userStory,
        steps: steps
      });
      
      addLog(`✅ User story completed successfully`, 'success');
      
      // Check if any screenshots were taken
      if (result.data && result.data.results) {
        const screenshots = result.data.results.filter(r => r.action === 'screenshot');
        if (screenshots.length > 0) {
          setScreenshotData(screenshots[screenshots.length - 1].screenshot);
        }
      }
      
    } catch (err) {
      addLog(`❌ User story failed: ${err.message}`, 'error');
    } finally {
      setIsRunning(false);
    }
  };

  const handleTakeScreenshot = async () => {
    try {
      addLog('📸 Taking screenshot...', 'info');
      const result = await apiCall('/take-screenshot', 'POST');
      
      if (result.data && result.data.screenshot) {
        setScreenshotData(result.data.screenshot);
        addLog(`✅ Screenshot taken - ${result.data.page_title}`, 'success');
      }
    } catch (err) {
      addLog(`❌ Screenshot failed: ${err.message}`, 'error');
    }
  };

  const addStep = () => {
    setSteps(prev => [...prev, {
      action: 'navigate',
      description: '',
      url: '',
      selector: '',
      text: ''
    }]);
  };

  const updateStep = (index, field, value) => {
    setSteps(prev => prev.map((step, i) => 
      i === index ? { ...step, [field]: value } : step
    ));
  };

  const removeStep = (index) => {
    setSteps(prev => prev.filter((_, i) => i !== index));
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'navigate': return <Globe className="w-4 h-4" />;
      case 'click': return <MousePointer className="w-4 h-4" />;
      case 'type': return <Type className="w-4 h-4" />;
      case 'wait': return <Clock className="w-4 h-4" />;
      case 'screenshot': return <Camera className="w-4 h-4" />;
      default: return <Play className="w-4 h-4" />;
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(() => {
      fetchLogs();
      if (!isRunning) {
        checkStatus();
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [isRunning]);

  return (
    <div className="max-w-7xl mx-auto p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2 flex items-center gap-3">
          <Globe className="w-8 h-8 text-blue-600" />
          Playwright Automation
        </h1>
        <p className="text-gray-600 mb-4">Execute user stories with automated browser testing</p>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${status.is_initialized ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600">
              {status.is_initialized ? 'Ready' : 'Not Ready'}
            </span>
          </div>
          
          {status.is_running && (
            <div className="flex items-center gap-2">
              <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
              <span className="text-sm text-blue-600">Running...</span>
            </div>
          )}
          
          {error && (
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{error}</span>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel - User Story Builder */}
        <div className="space-y-6">
          {/* User Story Input */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">User Story</h3>
            <textarea
              value={userStory}
              onChange={(e) => setUserStory(e.target.value)}
              placeholder="Describe what you want to test..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
            />
          </div>

          {/* Steps Builder */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">Steps</h3>
              <button
                onClick={addStep}
                className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-lg flex items-center gap-2 text-sm"
              >
                <Plus className="w-4 h-4" />
                Add Step
              </button>
            </div>
            
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {steps.map((step, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {getActionIcon(step.action)}
                      <span className="font-medium text-sm">Step {index + 1}</span>
                    </div>
                    <button
                      onClick={() => removeStep(index)}
                      className="text-red-600 hover:bg-red-50 p-1 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="space-y-2">
                    <select
                      value={step.action}
                      onChange={(e) => updateStep(index, 'action', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                    >
                      <option value="navigate">Navigate</option>
                      <option value="click">Click</option>
                      <option value="type">Type</option>
                      <option value="wait">Wait</option>
                      <option value="screenshot">Screenshot</option>
                    </select>
                    
                    <input
                      type="text"
                      value={step.description || ''}
                      onChange={(e) => updateStep(index, 'description', e.target.value)}
                      placeholder="Description"
                      className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                    />
                    
                    {step.action === 'navigate' && (
                      <input
                        type="url"
                        value={step.url || ''}
                        onChange={(e) => updateStep(index, 'url', e.target.value)}
                        placeholder="https://example.com"
                        className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                      />
                    )}
                    
                    {(step.action === 'click' || step.action === 'type' || step.action === 'wait') && (
                      <input
                        type="text"
                        value={step.selector || ''}
                        onChange={(e) => updateStep(index, 'selector', e.target.value)}
                        placeholder="CSS selector (e.g., #button, .class)"
                        className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                      />
                    )}
                    
                    {step.action === 'type' && (
                      <input
                        type="text"
                        value={step.text || ''}
                        onChange={(e) => updateStep(index, 'text', e.target.value)}
                        placeholder="Text to type"
                        className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={handleRunPlaywright}
                disabled={isRunning || !status.is_initialized}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-lg flex items-center justify-center gap-2 font-medium"
              >
                <Play className="w-5 h-5" />
                {isRunning ? 'Running...' : 'Run Story'}
              </button>
              
              <button
                onClick={handleTakeScreenshot}
                disabled={isRunning || !status.is_initialized}
                className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white px-6 py-3 rounded-lg flex items-center justify-center gap-2 font-medium"
              >
                <Camera className="w-5 h-5" />
                Screenshot
              </button>
            </div>
          </div>
        </div>

        {/* Right Panel - Logs and Screenshot */}
        <div className="space-y-6">
          {/* Live Logs */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              Live Logs
            </h3>
            <div className="bg-black rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm">
              {logs.length === 0 ? (
                <div className="text-gray-500">Waiting for activity...</div>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className={`mb-1 ${
                    log.type === 'error' ? 'text-red-400' :
                    log.type === 'success' ? 'text-green-400' :
                    'text-gray-300'
                  }`}>
                    <span className="text-gray-500 text-xs">{log.timestamp}</span> {log.message}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Screenshot Preview */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Monitor className="w-5 h-5" />
              Screenshot
            </h3>
            <div className="border-2 border-dashed border-gray-300 rounded-lg h-80 flex items-center justify-center bg-gray-50">
              {screenshotData ? (
                <img
                  src={`data:image/png;base64,${screenshotData}`}
                  alt="Page Screenshot"
                  className="max-w-full max-h-full object-contain rounded cursor-pointer"
                  onClick={() => {
                    const link = document.createElement('a');
                    link.href = `data:image/png;base64,${screenshotData}`;
                    link.download = `screenshot-${Date.now()}.png`;
                    link.click();
                  }}
                />
              ) : (
                <div className="text-center text-gray-500">
                  <Camera className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No screenshot yet</p>
                  <p className="text-sm">Screenshots will appear here</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlaywrightController;