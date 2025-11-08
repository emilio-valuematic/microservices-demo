import React, { useState, useEffect } from 'react';
import { Container, Navbar, Card, Form, Button, Badge, Row, Col, Spinner, Alert } from 'react-bootstrap';
import { RefreshCw, Settings, Play } from 'react-feather';
import { ToastContainer, toast } from 'react-toastify';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';
import ShapeSelector from './components/ShapeSelector';
import ParameterForm from './components/ParameterForm';
import api from './utils/api';

function App() {
  const [shapes, setShapes] = useState({});
  const [currentConfig, setCurrentConfig] = useState({});
  const [selectedShape, setSelectedShape] = useState('cyclic');
  const [parameters, setParameters] = useState({});
  const [noisePercent, setNoisePercent] = useState(0);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);

  // Load shapes and current config on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load available shapes
      const shapesResponse = await api.get('/api/shapes');
      setShapes(shapesResponse.data.shapes || {});

      // Load current config
      const configResponse = await api.get('/api/config');
      const config = configResponse.data.config || {};
      setCurrentConfig(config);

      // Set current shape
      const currentShape = configResponse.data.current_shape || 'cyclic';
      setSelectedShape(currentShape);

      // Extract noise percent
      const noise = parseFloat(config.NOISE_PERCENT || '0');
      setNoisePercent(noise);

      // Extract parameters for current shape
      const shapeParams = extractShapeParameters(currentShape, config);
      setParameters(shapeParams);

      toast.success('Configuration loaded successfully');
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error(`Failed to load configuration: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const extractShapeParameters = (shapeName, config) => {
    const params = {};
    const shapeMetadata = shapes[shapeName];

    if (!shapeMetadata || !shapeMetadata.parameters) {
      return params;
    }

    shapeMetadata.parameters.forEach(param => {
      if (config[param.name] !== undefined) {
        // Parse value based on type
        let value = config[param.name];
        if (param.type === 'json') {
          try {
            value = JSON.parse(value);
          } catch (e) {
            value = param.default;
          }
        } else if (param.type === 'int') {
          value = parseInt(value, 10);
        } else if (param.type === 'float') {
          value = parseFloat(value);
        }
        params[param.name] = value;
      } else {
        params[param.name] = param.default;
      }
    });

    return params;
  };

  const handleShapeChange = (shapeName) => {
    setSelectedShape(shapeName);

    // Load default parameters for new shape
    const shapeMetadata = shapes[shapeName];
    if (shapeMetadata && shapeMetadata.parameters) {
      const defaultParams = {};
      shapeMetadata.parameters.forEach(param => {
        defaultParams[param.name] = param.default;
      });
      setParameters(defaultParams);
    }
  };

  const handleParameterChange = (paramName, value) => {
    setParameters(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  const handleApplyConfig = async () => {
    setApplying(true);
    try {
      // Build configuration payload
      const config = {
        LOAD_SHAPE_TYPE: selectedShape,
        NOISE_PERCENT: noisePercent.toString(),
        ...parameters
      };

      // Convert complex types to strings
      Object.keys(config).forEach(key => {
        const value = config[key];
        if (typeof value === 'object') {
          config[key] = JSON.stringify(value);
        } else if (typeof value !== 'string') {
          config[key] = String(value);
        }
      });

      // Send to API
      await api.put('/api/config', config);

      toast.success('Configuration applied! Load generator is restarting...', {
        autoClose: 5000
      });

      // Reload config after a delay
      setTimeout(() => {
        loadData();
      }, 3000);

    } catch (error) {
      console.error('Error applying configuration:', error);
      toast.error(`Failed to apply configuration: ${error.message}`);
    } finally {
      setApplying(false);
    }
  };

  const handleRestart = async () => {
    try {
      await api.post('/api/restart');
      toast.success('Load generator is restarting...');
    } catch (error) {
      console.error('Error restarting:', error);
      toast.error(`Failed to restart: ${error.message}`);
    }
  };

  if (loading) {
    return (
      <div className="App">
        <Container>
          <div className="loading-container">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
          </div>
        </Container>
      </div>
    );
  }

  return (
    <div className="App">
      <Navbar variant="dark" expand="lg">
        <Container fluid>
          <Navbar.Brand>
            <Settings size={24} className="me-2" />
            Load Generator Dashboard
          </Navbar.Brand>
          <div className="d-flex align-items-center">
            <span className="status-indicator status-active"></span>
            <span className="text-secondary me-3">Connected</span>
            <Button
              variant="outline-primary"
              size="sm"
              onClick={loadData}
              disabled={loading}
            >
              <RefreshCw size={16} className="me-1" />
              Refresh
            </Button>
          </div>
        </Container>
      </Navbar>

      <Container className="mt-4">
        <Row>
          <Col lg={12}>
            <Card className="glow-card mb-4">
              <Card.Header>
                <h4 className="mb-0">
                  <i className="bi bi-graph-up me-2"></i>
                  Load Shape Configuration
                </h4>
              </Card.Header>
              <Card.Body>
                <Alert variant="info" className="mb-4">
                  <i className="bi bi-info-circle me-2"></i>
                  Select a load shape pattern and configure its parameters. Changes will restart the load generator pod.
                </Alert>

                {/* Shape Selector */}
                <ShapeSelector
                  shapes={shapes}
                  selectedShape={selectedShape}
                  onShapeChange={handleShapeChange}
                />

                {/* Parameter Form */}
                {shapes[selectedShape] && (
                  <ParameterForm
                    shape={shapes[selectedShape]}
                    parameters={parameters}
                    onParameterChange={handleParameterChange}
                  />
                )}

                {/* Noise Slider */}
                <div className="noise-slider">
                  <Row className="align-items-center">
                    <Col md={3}>
                      <Form.Label className="mb-0">
                        <i className="bi bi-activity me-2"></i>
                        Noise Level
                      </Form.Label>
                      <div className="text-secondary" style={{fontSize: '0.85rem'}}>
                        Add randomness to user count
                      </div>
                    </Col>
                    <Col md={7}>
                      <Form.Range
                        value={noisePercent}
                        onChange={(e) => setNoisePercent(parseFloat(e.target.value))}
                        min={0}
                        max={100}
                        step={1}
                      />
                    </Col>
                    <Col md={2}>
                      <div className="noise-value text-center">
                        {noisePercent.toFixed(0)}%
                      </div>
                    </Col>
                  </Row>
                </div>

                {/* Action Buttons */}
                <div className="action-buttons">
                  <Button
                    variant="outline-primary"
                    onClick={handleRestart}
                  >
                    <RefreshCw size={16} className="me-2" />
                    Restart Only
                  </Button>
                  <Button
                    variant="primary"
                    size="lg"
                    onClick={handleApplyConfig}
                    disabled={applying}
                  >
                    {applying ? (
                      <>
                        <Spinner
                          as="span"
                          animation="border"
                          size="sm"
                          role="status"
                          aria-hidden="true"
                          className="me-2"
                        />
                        Applying...
                      </>
                    ) : (
                      <>
                        <Play size={16} className="me-2" />
                        Apply Configuration & Restart
                      </>
                    )}
                  </Button>
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Current Configuration Display */}
        <Row>
          <Col lg={12}>
            <Card className="glow-card">
              <Card.Header>
                <h5 className="mb-0">
                  <i className="bi bi-code-square me-2"></i>
                  Current Configuration
                </h5>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col md={6}>
                    <p className="mb-2">
                      <strong className="text-cyan">Active Shape:</strong>{' '}
                      <Badge bg="secondary" className="badge-shape ms-2">
                        {currentConfig.LOAD_SHAPE_TYPE || selectedShape}
                      </Badge>
                    </p>
                    <p className="mb-2">
                      <strong className="text-cyan">Noise Level:</strong>{' '}
                      <span className="text-purple monospace">
                        {currentConfig.NOISE_PERCENT || '0'}%
                      </span>
                    </p>
                  </Col>
                  <Col md={6}>
                    <p className="mb-2">
                      <strong className="text-cyan">Deployment:</strong>{' '}
                      <code>{currentConfig.deployment_name || 'loadgenerator'}</code>
                    </p>
                    <p className="mb-2">
                      <strong className="text-cyan">Namespace:</strong>{' '}
                      <code>{currentConfig.namespace || 'default'}</code>
                    </p>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>

      <ToastContainer
        position="bottom-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
      />
    </div>
  );
}

export default App;
