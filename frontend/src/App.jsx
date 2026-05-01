import React, { useState, useEffect } from 'react';
import { Settings, Play, Download, AlertTriangle, CheckCircle, Calculator, FileText, Plus, Trash2, ChevronRight, Sun, Moon, GraduationCap } from 'lucide-react';

const getVariableName = (index, totalVars) => {
  return `x${index + 1}`;
};

const Label = ({ children }) => (
  <span style={{
    fontSize: '11px', fontWeight: 600, letterSpacing: '0.08em',
    textTransform: 'uppercase', color: 'var(--text-muted)'
  }}>
    {children}
  </span>
);

const Select = ({ name, value, onChange, children }) => (
  <select
    name={name} value={value} onChange={onChange}
    style={{
      width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius)', padding: '9px 12px', color: 'var(--text-primary)',
      fontSize: '13px', outline: 'none', cursor: 'pointer', transition: 'border-color 0.15s',
      appearance: 'auto'
    }}
    onFocus={e => e.target.style.borderColor = 'var(--accent)'}
    onBlur={e => e.target.style.borderColor = 'var(--border)'}
  >
    {children}
  </select>
);

const NumInput = ({ value, onChange, width = 64 }) => (
  <input
    type="number" step="1" value={value} onChange={onChange}
    style={{
      width, background: 'var(--bg-input)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-sm)', padding: '7px 8px', color: 'var(--text-primary)',
      fontSize: '13px', outline: 'none', textAlign: 'center', transition: 'border-color 0.15s'
    }}
    onFocus={e => e.target.style.borderColor = 'var(--accent)'}
    onBlur={e => e.target.style.borderColor = 'var(--border)'}
  />
);

const TextInput = ({ value, onChange, placeholder, width = '100%' }) => (
  <input
    type="text" value={value} onChange={onChange} placeholder={placeholder}
    style={{
      width, background: 'var(--bg-input)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-sm)', padding: '7px 12px', color: 'var(--text-primary)',
      fontSize: '13px', outline: 'none', transition: 'border-color 0.15s'
    }}
    onFocus={e => e.target.style.borderColor = 'var(--accent)'}
    onBlur={e => e.target.style.borderColor = 'var(--border)'}
  />
);

const Card = ({ children, style = {} }) => (
  <div style={{
    background: 'var(--bg-surface)', border: '1px solid var(--border)',
    borderRadius: 'var(--radius-xl)', boxShadow: 'var(--shadow-md)',
    overflow: 'hidden', ...style
  }}>
    {children}
  </div>
);

const CardHeader = ({ children }) => (
  <div style={{
    padding: '18px 24px', borderBottom: '1px solid var(--border)',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    gap: 12, background: 'var(--bg-elevated)'
  }}>
    {children}
  </div>
);

const Badge = ({ children, color = 'var(--accent)' }) => (
  <span style={{
    fontSize: '11px', fontWeight: 500, padding: '3px 8px',
    borderRadius: 99, background: `${color}20`, color,
    border: `1px solid ${color}40`, letterSpacing: '0.04em'
  }}>
    {children}
  </span>
);

const Divider = () => (
  <div style={{ height: 1, background: 'var(--border-subtle)', margin: '4px 0' }} />
);

function App() {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  const [formData, setFormData] = useState({
    tipo_objetivo: 'max',
    tipo_solucion: 'unica',
    tipo_restricciones: 'aleatorias',
    num_variables: 2,
    num_restricciones: 3
  });

  const [examInfo, setExamInfo] = useState({
    nombre: '',
    matricula: ''
  });

  const [objectiveCoeffs, setObjectiveCoeffs] = useState([3, 5]);

  const [customConstraints, setCustomConstraints] = useState([
    { coeficientes: [1, 0], operador: "<=", valor: 4 },
    { coeficientes: [0, 2], operador: "<=", valor: 12 }
  ]);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleExamInfoChange = (e) => {
    const { name, value } = e.target;
    setExamInfo({ ...examInfo, [name]: value });
  };

  const handleObjectiveCoeffChange = (index, value) => {
    const updated = [...objectiveCoeffs];
    updated[index] = Number(value);
    setObjectiveCoeffs(updated);
  };

  useEffect(() => {
    const newCoeffs = Array.from({ length: formData.num_variables }, (_, i) => 
      objectiveCoeffs[i] || 3
    );
    setObjectiveCoeffs(newCoeffs);
  }, [formData.num_variables]);

  useEffect(() => {
    const numRes = formData.num_restricciones;
    const numVars = formData.num_variables;
    const newConstraints = Array.from({ length: numRes }, (_, i) => {
      if (customConstraints[i]) {
        const coef = [...customConstraints[i].coeficientes];
        while (coef.length < numVars) coef.push(0);
        return { ...customConstraints[i], coeficientes: coef.slice(0, numVars) };
      }
      return { coeficientes: Array(numVars).fill(0), operador: "<=", valor: 0 };
    });
    setCustomConstraints(newConstraints);
  }, [formData.num_restricciones, formData.num_variables]);

  const handleConstraintChange = (index, field, value) => {
    const updated = [...customConstraints];
    if (field === 'coeficientes') {
      updated[index].coeficientes = value;
    } else if (field === 'operador') {
      updated[index].operador = value;
    } else if (field === 'valor') {
      updated[index].valor = Number(value);
    }
    setCustomConstraints(updated);
  };

  const handleCoefChange = (constraintIndex, varIndex, value) => {
    const updated = [...customConstraints];
    updated[constraintIndex].coeficientes[varIndex] = Number(value);
    setCustomConstraints(updated);
  };

  const addConstraint = () => {
    const newConstraint = {
      coeficientes: Array(formData.num_variables).fill(0),
      operador: "<=",
      valor: 0
    };
    setCustomConstraints([...customConstraints, newConstraint]);
  };

  const removeConstraint = (index) => {
    if (customConstraints.length <= 1) return;
    setCustomConstraints(customConstraints.filter((_, i) => i !== index));
  };

  const generateProblem = async () => {
    setLoading(true); setError(null); setResult(null);
    
    const requestPayload = { 
      ...formData,
      num_variables: Number(formData.num_variables),
      num_restricciones: Number(formData.num_restricciones)
    };
    
    if (formData.tipo_restricciones === 'fijas') {
      requestPayload.restricciones_custom = customConstraints;
      requestPayload.funcion_objetivo_custom = objectiveCoeffs;
    }
    
    try {
      const res = await fetch('http://localhost:8000/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestPayload),
      });
      if (!res.ok) throw new Error("Error en el backend. Verifica los parámetros ingresados.");
      setResult(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = () => {
    if (!result?.pdf_base64) return;
    const a = document.createElement('a');
    a.href = `data:application/pdf;base64,${result.pdf_base64}`;
    a.download = 'problema_examen.pdf';
    a.click();
  };

  const solucionLabels = {
    unica: 'Solución Única', multiple: 'Múltiples Soluciones',
    sin_solucion: 'Infactible', no_acotada: 'No Acotada'
  };

  const solucionColors = {
    unica: '#34d399', multiple: '#60a5fa',
    sin_solucion: '#f87171', no_acotada: '#fbbf24'
  };

  const varHeaders = Array.from({ length: formData.num_variables }, (_, i) => 
    getVariableName(i, formData.num_variables)
  );

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg-base)',
      padding: '32px 24px', fontFamily: 'Inter, sans-serif'
    }}>
      <div style={{ maxWidth: 1160, margin: '0 auto' }}>

        <header style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          marginBottom: 32, paddingBottom: 24,
          borderBottom: '1px solid var(--border)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{
              width: 44, height: 44, borderRadius: 12,
              background: 'var(--accent-subtle)', border: '1px solid var(--accent-border)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--accent)'
            }}>
              <Calculator size={22} />
            </div>
            <div>
              <h1 style={{
                fontSize: 22, fontWeight: 700, color: 'var(--text-primary)',
                letterSpacing: '-0.02em', lineHeight: 1
              }}>
                PIA - Programación Lineal
              </h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 3 }}>
                Generador de Exámenes · Método Simplex
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Badge color="var(--accent)">v2.0</Badge>
            <button
              onClick={() => setIsDark(d => !d)}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                width: 36, height: 36, borderRadius: 'var(--radius)',
                background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                color: 'var(--text-secondary)', cursor: 'pointer',
                transition: 'all 0.2s', flexShrink: 0
              }}
              onMouseEnter={e => e.currentTarget.style.color = 'var(--accent)'}
              onMouseLeave={e => e.currentTarget.style.color = 'var(--text-secondary)'}
            >
              {isDark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
          </div>
        </header>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 480px) minmax(0, 1fr)',
          gap: 20, alignItems: 'start'
        }}>

          <Card>
            <CardHeader>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Settings size={15} color="var(--text-muted)" />
                <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>
                  Configuración del Examen
                </span>
              </div>
            </CardHeader>

            <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 18 }}>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                  <Label>Variables</Label>
                  <Select name="num_variables" value={formData.num_variables} onChange={handleChange}>
                    {[2,3,4,5,6,7,8,9,10].map(n => (
                      <option key={n} value={n}>{n} {n === 2 ? '(x, y)' : n === 3 ? '(x, y, z)' : ''}</option>
                    ))}
                  </Select>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                  <Label>Restricciones</Label>
                  <Select name="num_restricciones" value={formData.num_restricciones} onChange={handleChange}>
                    {[1,2,3,4,5,6,7,8,9,10].map(n => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </Select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                  <Label>Objetivo</Label>
                  <Select name="tipo_objetivo" value={formData.tipo_objetivo} onChange={handleChange}>
                    <option value="max">Maximizar Z</option>
                    <option value="min">Minimizar Z</option>
                  </Select>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                  <Label>Tipo de Solución</Label>
                  <Select name="tipo_solucion" value={formData.tipo_solucion} onChange={handleChange}>
                    <option value="unica">Única</option>
                    <option value="multiple">Múltiple</option>
                    <option value="sin_solucion">Infactible</option>
                    <option value="no_acotada">No Acotada</option>
                  </Select>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                <Label>Modalidad de Restricciones</Label>
                <Select name="tipo_restricciones" value={formData.tipo_restricciones} onChange={handleChange}>
                  <option value="aleatorias">Generación Aleatoria</option>
                  <option value="fijas">Carga Manual</option>
                </Select>
              </div>

              {formData.tipo_restricciones === 'fijas' && (
                <>
                  <Divider />
                  
                  <div>
                    <Label>Función Objetivo</Label>
                    <div style={{ 
                      display: 'flex', alignItems: 'center', gap: 8, marginTop: 8,
                      flexWrap: 'wrap'
                    }}>
                      <Select 
                        name="tipo_objetivo" 
                        value={formData.tipo_objetivo} 
                        onChange={handleChange}
                        style={{ width: 100 }}
                      >
                        <option value="max">Max Z =</option>
                        <option value="min">Min Z =</option>
                      </Select>
                      {objectiveCoeffs.map((coef, i) => (
                        <React.Fragment key={i}>
                          <NumInput
                            value={coef}
                            onChange={(e) => handleObjectiveCoeffChange(i, e.target.value)}
                            width={50}
                          />
                          <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
                            {getVariableName(i, formData.num_variables)}
                          </span>
                          {i < objectiveCoeffs.length - 1 && <span style={{ color: 'var(--text-muted)' }}>+</span>}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>

                  <div>
                    <div style={{
                      display: 'flex', justifyContent: 'space-between',
                      alignItems: 'center', marginBottom: 12
                    }}>
                      <Label>Matriz de Restricciones</Label>
                      <button
                        onClick={addConstraint}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 4,
                          background: 'var(--accent-subtle)', border: '1px solid var(--accent-border)',
                          borderRadius: 'var(--radius-sm)', padding: '4px 10px',
                          color: 'var(--accent)', fontSize: 12, fontWeight: 500,
                          cursor: 'pointer', transition: 'all 0.15s'
                        }}
                      >
                        <Plus size={13} /> Fila
                      </button>
                    </div>

                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: `repeat(${formData.num_variables}, 50px) 12px 40px 50px 28px`,
                      gap: 4, padding: '0 4px 8px',
                      alignItems: 'center', justifyItems: 'center'
                    }}>
                      {varHeaders.map((h, i) => (
                        <span key={i} style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>{h}</span>
                      ))}
                      <span></span>
                      <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>op</span>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>val</span>
                      <span></span>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {customConstraints.map((c, idx) => (
                        <div key={idx} style={{
                          display: 'grid',
                          gridTemplateColumns: `repeat(${formData.num_variables}, 50px) 12px 40px 50px 28px`,
                          gap: 4, alignItems: 'center', justifyItems: 'center',
                          background: 'var(--bg-elevated)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius)', padding: '8px 6px'
                        }}>
                          {c.coeficientes.map((coef, varIdx) => (
                            <NumInput
                              key={varIdx}
                              value={coef}
                              onChange={(e) => handleCoefChange(idx, varIdx, e.target.value)}
                              width={46}
                            />
                          ))}
                          <select
                            value={c.operador}
                            onChange={(e) => handleConstraintChange(idx, 'operador', e.target.value)}
                            style={{
                              width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)',
                              borderRadius: 'var(--radius-sm)', padding: '6px 2px', color: 'var(--text-primary)',
                              fontSize: 12, outline: 'none', textAlign: 'center'
                            }}
                          >
                            <option value="<=">≤</option>
                            <option value=">=">≥</option>
                            <option value="=">=</option>
                          </select>
                          <NumInput width={46} value={c.valor} onChange={(e) => handleConstraintChange(idx, 'valor', e.target.value)} />
                          <button
                            onClick={() => removeConstraint(idx)}
                            style={{
                              background: 'none', border: 'none', cursor: 'pointer',
                              color: 'var(--text-muted)', padding: 4,
                              borderRadius: 'var(--radius-sm)', transition: 'color 0.15s',
                              display: 'flex', alignItems: 'center'
                            }}
                            onMouseEnter={e => e.currentTarget.style.color = 'var(--red)'}
                            onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              <button
                onClick={generateProblem}
                disabled={loading}
                style={{
                  marginTop: 4, width: '100%', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', gap: 8,
                  background: loading ? '#2d3a5c' : 'var(--accent)',
                  border: 'none', borderRadius: 'var(--radius)', padding: '11px 20px',
                  color: '#fff', fontSize: 14, fontWeight: 600,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s', opacity: loading ? 0.7 : 1,
                  boxShadow: loading ? 'none' : '0 0 20px rgba(79,110,247,0.25)'
                }}
                onMouseEnter={e => { if (!loading) e.currentTarget.style.background = 'var(--accent-hover)'; }}
                onMouseLeave={e => { if (!loading) e.currentTarget.style.background = 'var(--accent)'; }}
              >
                {loading
                  ? <div style={{
                      width: 16, height: 16, border: '2px solid rgba(255,255,255,0.3)',
                      borderTopColor: '#fff', borderRadius: '50%',
                      animation: 'spin 0.7s linear infinite'
                    }} />
                  : <Play size={15} />
                }
                {loading ? 'Procesando…' : 'Generar Problema'}
              </button>
            </div>
          </Card>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {error && (
              <div style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                background: 'var(--red-subtle)', border: '1px solid var(--red-border)',
                borderRadius: 'var(--radius-lg)', padding: '14px 16px',
                color: 'var(--red)', fontSize: 13
              }}>
                <AlertTriangle size={16} style={{ marginTop: 1, flexShrink: 0 }} />
                <span>{error}</span>
              </div>
            )}

            {!result && !loading && !error && (
              <Card style={{ minHeight: 480 }}>
                <div style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center',
                  justifyContent: 'center', height: '100%', minHeight: 480,
                  gap: 12, color: 'var(--text-muted)'
                }}>
                  <div style={{
                    width: 56, height: 56, borderRadius: '50%',
                    background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <FileText size={24} strokeWidth={1.5} />
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <p style={{ color: 'var(--text-secondary)', fontWeight: 500, marginBottom: 4 }}>Vista Previa del Examen</p>
                    <p style={{ fontSize: 13, maxWidth: 280, lineHeight: 1.6 }}>
                      Configura los parámetros y haz clic en <em>Generar Problema</em> para ver el examen.
                    </p>
                  </div>
                </div>
              </Card>
            )}

            {result && !loading && (
              <>
                <Card>
                  <CardHeader>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <CheckCircle size={15} color="var(--green)" />
                      <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>
                        Examen Generado
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Badge color={solucionColors[formData.tipo_solucion]}>
                        {solucionLabels[formData.tipo_solucion]}
                      </Badge>
                      {result.pdf_base64 && (
                        <button
                          onClick={downloadPDF}
                          style={{
                            display: 'flex', alignItems: 'center', gap: 6,
                            background: 'var(--accent-subtle)', border: '1px solid var(--accent-border)',
                            borderRadius: 'var(--radius-sm)', padding: '6px 12px',
                            color: 'var(--accent)', fontSize: 12, fontWeight: 500,
                            cursor: 'pointer', transition: 'all 0.15s'
                          }}
                        >
                          <Download size={13} /> Descargar PDF
                        </button>
                      )}
                    </div>
                  </CardHeader>

                  <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
                    <div style={{
                      background: 'var(--bg-elevated)', borderRadius: 'var(--radius)',
                      border: '1px solid var(--border-subtle)', padding: '14px 16px'
                    }}>
                      <Label>Función Objetivo</Label>
                      <p style={{
                        marginTop: 8, fontFamily: 'JetBrains Mono, monospace',
                        fontSize: 15, fontWeight: 500, color: 'var(--green)'
                      }}>
                        {result.funcion_objetivo.string_repr}
                      </p>
                    </div>

                    <div style={{
                      background: 'var(--bg-elevated)', borderRadius: 'var(--radius)',
                      border: '1px solid var(--border-subtle)', padding: '14px 16px'
                    }}>
                      <Label>Restricciones ({result.num_restricciones})</Label>
                      <div style={{
                        marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4,
                        fontFamily: 'JetBrains Mono, monospace', fontSize: 13,
                        color: '#93bbfc'
                      }}>
                        {result.restricciones.map((r, i) => (
                          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <ChevronRight size={11} color="var(--text-muted)" style={{ flexShrink: 0 }} />
                            {r.string_repr}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>

                <Card>
                  <CardHeader>
                    <Label>Vista Previa LaTeX</Label>
                  </CardHeader>
                  <div style={{ padding: 4 }}>
                    <pre style={{
                      margin: 0, padding: '18px 20px',
                      background: 'var(--bg-base)',
                      fontFamily: 'JetBrains Mono, monospace',
                      fontSize: 12.5, lineHeight: 1.7,
                      color: '#a5b4d4', overflowX: 'auto',
                      borderRadius: 'var(--radius)',
                      whiteSpace: 'pre-wrap'
                    }}>
                      <code>{result.latex_code}</code>
                    </pre>
                  </div>
                </Card>
              </>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

export default App;