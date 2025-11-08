import React from 'react';
import { Form, Row, Col, InputGroup } from 'react-bootstrap';
import StagesEditor from './StagesEditor';

function ParameterForm({ shape, parameters, onParameterChange }) {
  if (!shape || !shape.parameters) {
    return null;
  }

  const renderParameter = (param) => {
    const value = parameters[param.name] ?? param.default;

    // Special handling for JSON parameters (like STAGES_JSON)
    if (param.type === 'json') {
      return (
        <StagesEditor
          key={param.name}
          stages={value}
          onChange={(newStages) => onParameterChange(param.name, newStages)}
          label={param.label}
          description={param.description}
        />
      );
    }

    // Standard input types
    return (
      <Form.Group key={param.name} className="mb-3">
        <Form.Label>
          {param.label}
          {param.description && (
            <small className="text-secondary ms-2">({param.description})</small>
          )}
        </Form.Label>
        <InputGroup>
          <Form.Control
            type="number"
            value={value}
            onChange={(e) => {
              const newValue = param.type === 'float'
                ? parseFloat(e.target.value)
                : parseInt(e.target.value, 10);
              onParameterChange(param.name, newValue);
            }}
            min={param.min}
            max={param.max}
            step={param.step || (param.type === 'float' ? 0.1 : 1)}
          />
          {param.unit && (
            <InputGroup.Text>{param.unit}</InputGroup.Text>
          )}
        </InputGroup>
        {param.help && (
          <Form.Text className="text-secondary">
            {param.help}
          </Form.Text>
        )}
      </Form.Group>
    );
  };

  return (
    <div className="parameter-form mt-4 mb-4">
      <h5 className="mb-3">
        <i className="bi bi-sliders me-2"></i>
        Parameters for {shape.name}
      </h5>
      <Row>
        {shape.parameters.map((param) => (
          <Col md={6} lg={4} key={param.name}>
            {renderParameter(param)}
          </Col>
        ))}
      </Row>
    </div>
  );
}

export default ParameterForm;
