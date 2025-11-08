import React from 'react';
import { Card, Form, Button, Row, Col, InputGroup } from 'react-bootstrap';
import { Plus, Trash2 } from 'react-feather';

function StagesEditor({ stages, onChange, label, description }) {
  const handleStageChange = (index, field, value) => {
    const newStages = [...stages];
    newStages[index][field] = field === 'spawn_rate' ? parseFloat(value) : parseInt(value, 10);
    onChange(newStages);
  };

  const addStage = () => {
    const lastStage = stages[stages.length - 1];
    const newDuration = lastStage ? lastStage.duration + 60 : 60;
    onChange([
      ...stages,
      { duration: newDuration, users: 10, spawn_rate: 10 }
    ]);
  };

  const removeStage = (index) => {
    if (stages.length > 1) {
      const newStages = stages.filter((_, i) => i !== index);
      onChange(newStages);
    }
  };

  return (
    <div className="stages-editor mb-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h6 className="mb-0">{label}</h6>
          {description && (
            <small className="text-secondary">{description}</small>
          )}
        </div>
        <Button
          variant="outline-primary"
          size="sm"
          onClick={addStage}
        >
          <Plus size={16} className="me-1" />
          Add Stage
        </Button>
      </div>

      <div className="stages-list">
        {stages.map((stage, index) => (
          <Card key={index} className="mb-2" style={{ backgroundColor: 'var(--darker-navy)', border: '1px solid var(--glow-purple)' }}>
            <Card.Body className="py-2">
              <Row className="align-items-center">
                <Col xs={1}>
                  <strong className="text-cyan">#{index + 1}</strong>
                </Col>
                <Col xs={10}>
                  <Row>
                    <Col md={4}>
                      <Form.Group>
                        <Form.Label className="small mb-1">Duration (sec)</Form.Label>
                        <Form.Control
                          type="number"
                          size="sm"
                          value={stage.duration}
                          onChange={(e) => handleStageChange(index, 'duration', e.target.value)}
                          min={1}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={4}>
                      <Form.Group>
                        <Form.Label className="small mb-1">Users</Form.Label>
                        <Form.Control
                          type="number"
                          size="sm"
                          value={stage.users}
                          onChange={(e) => handleStageChange(index, 'users', e.target.value)}
                          min={0}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={4}>
                      <Form.Group>
                        <Form.Label className="small mb-1">Spawn Rate</Form.Label>
                        <Form.Control
                          type="number"
                          size="sm"
                          value={stage.spawn_rate}
                          onChange={(e) => handleStageChange(index, 'spawn_rate', e.target.value)}
                          min={0.1}
                          step={0.1}
                        />
                      </Form.Group>
                    </Col>
                  </Row>
                </Col>
                <Col xs={1} className="text-end">
                  <Button
                    variant="outline-danger"
                    size="sm"
                    onClick={() => removeStage(index)}
                    disabled={stages.length === 1}
                  >
                    <Trash2 size={14} />
                  </Button>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default StagesEditor;
