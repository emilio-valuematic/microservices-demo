import React from 'react';
import { Row, Col, Card } from 'react-bootstrap';
import { TrendingUp, Zap, Activity, BarChart2, Layers } from 'react-feather';

const SHAPE_ICONS = {
  cyclic: TrendingUp,
  stages: Layers,
  spike: Zap,
  sinusoidal: Activity,
  step: BarChart2
};

function ShapeSelector({ shapes, selectedShape, onShapeChange }) {
  return (
    <div className="shape-selector">
      <h5 className="mb-3">
        <i className="bi bi-diagram-3 me-2"></i>
        Select Load Shape Pattern
      </h5>
      <Row>
        {Object.entries(shapes).map(([key, shape]) => {
          const Icon = SHAPE_ICONS[key] || Activity;
          const isSelected = key === selectedShape;

          return (
            <Col md={6} lg={4} key={key} className="mb-3">
              <Card
                className={`shape-option ${isSelected ? 'selected' : ''} h-100`}
                onClick={() => onShapeChange(key)}
                style={{ cursor: 'pointer' }}
              >
                <Card.Body>
                  <div className="d-flex align-items-center mb-2">
                    <Icon size={24} className="me-2" style={{ color: 'var(--accent-blue)' }} />
                    <Card.Title className="mb-0" style={{ fontSize: '1rem' }}>
                      {shape.name}
                    </Card.Title>
                  </div>
                  <p className="shape-description mb-0">
                    {shape.description}
                  </p>
                  {isSelected && (
                    <div className="mt-2">
                      <span className="badge badge-active">
                        <i className="bi bi-check-circle me-1"></i>
                        Selected
                      </span>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>
          );
        })}
      </Row>
    </div>
  );
}

export default ShapeSelector;
