# Ferramentas (gerado de `list_tools`; não edite à mão)

## `ae_get_project_overview`

_readOnly=True · destructive=None · idempotent=True_

Visão geral do projeto aberto: versão do AE, arquivo, se há alterações não salvas,
itens (comps com tamanho/duração/fps/nº de camadas; até 50) e fila de render.
Use SEMPRE antes de editar, para descobrir nomes e índices.

```json
{
  "type": "object",
  "properties": {
    "response_format": {
      "default": "concise",
      "description": "concise (padrão) ou detailed (mais campos).",
      "enum": [
        "concise",
        "detailed"
      ],
      "title": "Response Format",
      "type": "string"
    }
  },
  "title": "ae_get_project_overviewArguments"
}
```

## `ae_inspect_comp`

_readOnly=True · destructive=None · idempotent=True_

Lê uma composição: configurações e camadas (índice, nome, tipo, tempos, posição, opacidade,
texto, efeitos, propriedades animadas). 'detailed' acrescenta escala, rotação, âncora, fonte,
cor e os valores dos keyframes (até 20 por propriedade). Use para verificar o resultado de edições.

```json
{
  "type": "object",
  "properties": {
    "comp_name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Nome exato da composição. Use este OU comp_index.",
      "title": "Comp Name"
    },
    "comp_index": {
      "anyOf": [
        {
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Índice do item no painel Projeto (base 1), como em ae_get_project_overview.",
      "title": "Comp Index"
    },
    "response_format": {
      "default": "concise",
      "description": "concise (padrão) ou detailed (mais campos).",
      "enum": [
        "concise",
        "detailed"
      ],
      "title": "Response Format",
      "type": "string"
    }
  },
  "title": "ae_inspect_compArguments"
}
```

## `ae_create_comp`

_readOnly=False · destructive=False · idempotent=False_

Cria uma composição. Ex.: vertical 1080x1920, 10 s, 30 fps. Devolve comp_index e nome.

```json
{
  "type": "object",
  "properties": {
    "name": {
      "minLength": 1,
      "title": "Name",
      "type": "string"
    },
    "width": {
      "maximum": 30000,
      "minimum": 4,
      "title": "Width",
      "type": "integer"
    },
    "height": {
      "maximum": 30000,
      "minimum": 4,
      "title": "Height",
      "type": "integer"
    },
    "duration": {
      "description": "Segundos",
      "exclusiveMinimum": 0,
      "maximum": 10800,
      "title": "Duration",
      "type": "number"
    },
    "frame_rate": {
      "default": 30,
      "exclusiveMinimum": 0,
      "maximum": 999,
      "title": "Frame Rate",
      "type": "number"
    },
    "background_color": {
      "anyOf": [
        {
          "description": "Cor #RRGGBB, ex.: #F05378",
          "pattern": "^#[0-9A-Fa-f]{6}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Background Color"
    }
  },
  "required": [
    "name",
    "width",
    "height",
    "duration"
  ],
  "title": "ae_create_compArguments"
}
```

## `ae_add_layer`

_readOnly=False · destructive=False · idempotent=False_

Adiciona uma camada no topo da comp (vira layer_index 1; as outras descem um índice).
Texto nasce com a âncora na linha de base; para centralizar, use ae_set_layer_properties
com justification='center' e center_anchor=true.

```json
{
  "type": "object",
  "properties": {
    "layer_type": {
      "enum": [
        "text",
        "solid",
        "null_object",
        "adjustment",
        "shape_rectangle",
        "shape_ellipse"
      ],
      "title": "Layer Type",
      "type": "string"
    },
    "comp_name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Nome exato da composição. Use este OU comp_index.",
      "title": "Comp Name"
    },
    "comp_index": {
      "anyOf": [
        {
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Índice do item no painel Projeto (base 1), como em ae_get_project_overview.",
      "title": "Comp Index"
    },
    "text": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Obrigatório para layer_type=text.",
      "title": "Text"
    },
    "name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Name"
    },
    "color": {
      "anyOf": [
        {
          "pattern": "^#[0-9A-Fa-f]{6}$",
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "#RRGGBB: cor do sólido/shape ou do preenchimento do texto",
      "title": "Color"
    },
    "width": {
      "anyOf": [
        {
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Solid/shape; padrão = largura da comp.",
      "title": "Width"
    },
    "height": {
      "anyOf": [
        {
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Height"
    },
    "position": {
      "anyOf": [
        {
          "items": {
            "type": "number"
          },
          "maxItems": 3,
          "minItems": 2,
          "type": "array"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "[x, y] em pixels",
      "title": "Position"
    }
  },
  "required": [
    "layer_type"
  ],
  "title": "ae_add_layerArguments"
}
```

## `ae_set_layer_properties`

_readOnly=False · destructive=False · idempotent=True_

Altera várias camadas de uma vez (valores estáticos): nome, transform, tempos, texto, fonte,
cor, justificação, pai, âncora central e propriedades por caminho. Propriedades com keyframes
devem ser mudadas com ae_set_keyframes.

```json
{
  "type": "object",
  "$defs": {
    "LayerChange": {
      "properties": {
        "layer_index": {
          "minimum": 1,
          "title": "Layer Index",
          "type": "integer"
        },
        "name": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Name"
        },
        "position": {
          "anyOf": [
            {
              "items": {
                "type": "number"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Position"
        },
        "scale": {
          "anyOf": [
            {
              "items": {
                "type": "number"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Percentual, ex.: [100, 100]",
          "title": "Scale"
        },
        "rotation": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Rotation"
        },
        "opacity": {
          "anyOf": [
            {
              "maximum": 100,
              "minimum": 0,
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Opacity"
        },
        "anchor_point": {
          "anyOf": [
            {
              "items": {
                "type": "number"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Anchor Point"
        },
        "in_point": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "In Point"
        },
        "out_point": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Out Point"
        },
        "text": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Text"
        },
        "font": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Nome PostScript, ex.: Arial-BoldMT",
          "title": "Font"
        },
        "font_size": {
          "anyOf": [
            {
              "exclusiveMinimum": 0,
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Font Size"
        },
        "fill_color": {
          "anyOf": [
            {
              "description": "Cor #RRGGBB, ex.: #F05378",
              "pattern": "^#[0-9A-Fa-f]{6}$",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Fill Color"
        },
        "justification": {
          "anyOf": [
            {
              "enum": [
                "left",
                "center",
                "right"
              ],
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Justification"
        },
        "parent_index": {
          "anyOf": [
            {
              "minimum": 0,
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "0 remove o pai",
          "title": "Parent Index"
        },
        "center_anchor": {
          "anyOf": [
            {
              "type": "boolean"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Põe a âncora no centro visual da camada (útil para centralizar texto).",
          "title": "Center Anchor"
        },
        "properties": {
          "anyOf": [
            {
              "additionalProperties": {
                "anyOf": [
                  {
                    "type": "number"
                  },
                  {
                    "items": {
                      "type": "number"
                    },
                    "type": "array"
                  },
                  {
                    "type": "string"
                  }
                ]
              },
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "description": "Caminho → valor, ex.: {\"Effects/Gaussian Blur/Blurriness\": 20}",
          "title": "Properties"
        }
      },
      "required": [
        "layer_index"
      ],
      "title": "LayerChange",
      "type": "object"
    }
  },
  "properties": {
    "changes": {
      "items": {
        "$ref": "#/$defs/LayerChange"
      },
      "minItems": 1,
      "title": "Changes",
      "type": "array"
    },
    "comp_name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Nome exato da composição. Use este OU comp_index.",
      "title": "Comp Name"
    },
    "comp_index": {
      "anyOf": [
        {
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Índice do item no painel Projeto (base 1), como em ae_get_project_overview.",
      "title": "Comp Index"
    }
  },
  "required": [
    "changes"
  ],
  "title": "ae_set_layer_propertiesArguments"
}
```

## `ae_set_keyframes`

_readOnly=False · destructive=False · idempotent=True_

Cria keyframes em lote. Ex. de fade-in de 1 s: property='opacity',
keyframes=[{time:0,value:0},{time:1,value:100}], easing='ease'.

```json
{
  "type": "object",
  "$defs": {
    "Keyframe": {
      "properties": {
        "time": {
          "description": "Segundos",
          "minimum": 0,
          "title": "Time",
          "type": "number"
        },
        "value": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "items": {
                "type": "number"
              },
              "type": "array"
            },
            {
              "type": "string"
            }
          ],
          "title": "Value"
        }
      },
      "required": [
        "time",
        "value"
      ],
      "title": "Keyframe",
      "type": "object"
    },
    "Track": {
      "properties": {
        "layer_index": {
          "minimum": 1,
          "title": "Layer Index",
          "type": "integer"
        },
        "property": {
          "description": "position|scale|rotation|opacity|anchor_point ou caminho, ex.: 'Effects/Gaussian Blur/Blurriness'",
          "title": "Property",
          "type": "string"
        },
        "keyframes": {
          "items": {
            "$ref": "#/$defs/Keyframe"
          },
          "minItems": 1,
          "title": "Keyframes",
          "type": "array"
        },
        "easing": {
          "default": "linear",
          "enum": [
            "linear",
            "ease",
            "hold"
          ],
          "title": "Easing",
          "type": "string"
        },
        "replace_existing": {
          "default": true,
          "description": "Apaga os keyframes existentes da propriedade antes.",
          "title": "Replace Existing",
          "type": "boolean"
        }
      },
      "required": [
        "layer_index",
        "property",
        "keyframes"
      ],
      "title": "Track",
      "type": "object"
    }
  },
  "properties": {
    "tracks": {
      "items": {
        "$ref": "#/$defs/Track"
      },
      "minItems": 1,
      "title": "Tracks",
      "type": "array"
    },
    "comp_name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Nome exato da composição. Use este OU comp_index.",
      "title": "Comp Name"
    },
    "comp_index": {
      "anyOf": [
        {
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Índice do item no painel Projeto (base 1), como em ae_get_project_overview.",
      "title": "Comp Index"
    }
  },
  "required": [
    "tracks"
  ],
  "title": "ae_set_keyframesArguments"
}
```

## `ae_apply_effect`

_readOnly=False · destructive=False · idempotent=False_

Adiciona um efeito à camada e define parâmetros. Devolve a lista de parâmetros disponíveis.

```json
{
  "type": "object",
  "properties": {
    "layer_index": {
      "minimum": 1,
      "title": "Layer Index",
      "type": "integer"
    },
    "effect": {
      "description": "Nome em inglês ou matchName: 'Gaussian Blur', 'ADBE Fill', 'Glow'…",
      "title": "Effect",
      "type": "string"
    },
    "comp_name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Nome exato da composição. Use este OU comp_index.",
      "title": "Comp Name"
    },
    "comp_index": {
      "anyOf": [
        {
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Índice do item no painel Projeto (base 1), como em ae_get_project_overview.",
      "title": "Comp Index"
    },
    "params": {
      "anyOf": [
        {
          "additionalProperties": {
            "anyOf": [
              {
                "type": "number"
              },
              {
                "items": {
                  "type": "number"
                },
                "type": "array"
              },
              {
                "type": "string"
              }
            ]
          },
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Ex.: {\"Blurriness\": 15}; cores como \"#RRGGBB\"",
      "title": "Params"
    }
  },
  "required": [
    "layer_index",
    "effect"
  ],
  "title": "ae_apply_effectArguments"
}
```

## `ae_remove_layers`

_readOnly=False · destructive=True · idempotent=False_

Apaga camadas pelos índices (pode desfazer com Cmd+Z no AE). Confirme com o usuário se
as camadas não foram criadas nesta sessão.

```json
{
  "type": "object",
  "properties": {
    "layer_indexes": {
      "items": {
        "minimum": 1,
        "type": "integer"
      },
      "minItems": 1,
      "title": "Layer Indexes",
      "type": "array"
    },
    "comp_name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Nome exato da composição. Use este OU comp_index.",
      "title": "Comp Name"
    },
    "comp_index": {
      "anyOf": [
        {
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Índice do item no painel Projeto (base 1), como em ae_get_project_overview.",
      "title": "Comp Index"
    }
  },
  "required": [
    "layer_indexes"
  ],
  "title": "ae_remove_layersArguments"
}
```

## `ae_queue_render`

_readOnly=False · destructive=False · idempotent=False_

Adiciona a comp à fila de render. NÃO inicia o render: renderizar bloqueia o AE.
O usuário clica em Render no AE ou usa aerender.

```json
{
  "type": "object",
  "properties": {
    "output_path": {
      "description": "Caminho absoluto do arquivo de saída; a pasta deve existir.",
      "title": "Output Path",
      "type": "string"
    },
    "comp_name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Nome exato da composição. Use este OU comp_index.",
      "title": "Comp Name"
    },
    "comp_index": {
      "anyOf": [
        {
          "minimum": 1,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Índice do item no painel Projeto (base 1), como em ae_get_project_overview.",
      "title": "Comp Index"
    },
    "output_module_template": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Output Module Template"
    },
    "render_settings_template": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Render Settings Template"
    },
    "overwrite": {
      "default": false,
      "title": "Overwrite",
      "type": "boolean"
    }
  },
  "required": [
    "output_path"
  ],
  "title": "ae_queue_renderArguments"
}
```

## `ae_save_project_as`

_readOnly=False · destructive=True · idempotent=False_

Salva o projeto em um .aep. Recusa sobrescrever sem overwrite=true; só use overwrite
com a confirmação explícita do usuário.

```json
{
  "type": "object",
  "properties": {
    "path": {
      "description": "Caminho absoluto terminando em .aep",
      "title": "Path",
      "type": "string"
    },
    "overwrite": {
      "default": false,
      "title": "Overwrite",
      "type": "boolean"
    }
  },
  "required": [
    "path"
  ],
  "title": "ae_save_project_asArguments"
}
```

## `ae_new_project`

_readOnly=False · destructive=True · idempotent=False_

Fecha o projeto atual e começa um vazio. Recusa se houver alterações não salvas;
discard_unsaved_changes=true só com a confirmação explícita do usuário.

```json
{
  "type": "object",
  "properties": {
    "discard_unsaved_changes": {
      "default": false,
      "title": "Discard Unsaved Changes",
      "type": "boolean"
    }
  },
  "title": "ae_new_projectArguments"
}
```

## `ae_open_project`

_readOnly=False · destructive=True · idempotent=False_

Abre um .aep, com a mesma proteção de ae_new_project. Projetos com mídia ou fontes ausentes
podem abrir um diálogo no AE que bloqueia os próximos comandos até o usuário fechá-lo.

```json
{
  "type": "object",
  "properties": {
    "path": {
      "description": "Caminho absoluto de um .aep",
      "title": "Path",
      "type": "string"
    },
    "discard_unsaved_changes": {
      "default": false,
      "title": "Discard Unsaved Changes",
      "type": "boolean"
    }
  },
  "required": [
    "path"
  ],
  "title": "ae_open_projectArguments"
}
```

## `ae_run_extendscript`

_readOnly=False · destructive=True · idempotent=False_

VÁLVULA DE ESCAPE: executa ExtendScript arbitrário dentro de um undo group. Desligada por padrão
(AE_MCP_ENABLE_RUN_EXTENDSCRIPT=1 para habilitar). Prefira as ferramentas ae_*. Nunca use alert()
nem diálogos: eles travam o AE.

```json
{
  "type": "object",
  "properties": {
    "code": {
      "description": "Corpo de função ExtendScript (ES3); o valor do return é devolvido em JSON.",
      "title": "Code",
      "type": "string"
    }
  },
  "required": [
    "code"
  ],
  "title": "ae_run_extendscriptArguments"
}
```
