# Forest Walk

## Seminário

docs.google.com/presentation/d/1pxGF2tJd8qKPJCvGun1es88M5ME2hcnHr-qr4_5GJ38

---

## Visão Geral

**Forest Walk** é um projeto de jogo 3D em primeira pessoa desenvolvido em **Python**, utilizando uma **engine própria** inspirada na arquitetura do Godot Engine. O foco do projeto é a exploração de ambientes, com forte ênfase em imersão, atmosfera e sensação de presença, usando iluminação mínima, movimentação realista de câmera e sistemas de stamina.

O projeto serve tanto como **jogo experimental** quanto como **prova de conceito arquitetural** de uma engine modular baseada em Scene Graph, Nodes e componentes desacoplados.

---

## Arquitetura Geral

O projeto é dividido claramente em duas grandes camadas:

```
engine/  → Engine genérica (rendering, física, cena, UI, recursos)
game/    → Código específico do jogo (player, levels, entidades, HUD)
```

Essa separação segue princípios de **Clean Architecture**:

* A engine **não conhece** o jogo.
* O jogo apenas consome APIs públicas da engine.
* Sistemas são desacoplados e extensíveis.

A base do funcionamento é uma **árvore de nós (Scene Graph)**, onde tudo é um `Node` ou deriva de um.

---

## Estrutura de Pastas

### `engine/`

Contém toda a engine genérica reutilizável.

Principais submódulos:

* **core/**

  * Sistema base de objetos, recursos, input e notificações.

* **math/**

  * Vetores, matrizes, transformações, geometria e utilitários matemáticos.

* **scene/**

  * Implementação do Scene Graph.
  * Nodes 2D, 3D, câmera, luzes, física, timers e sinais.

* **resources/**

  * Recursos carregáveis: meshes, texturas, imagens, materiais, fontes.

* **servers/**

  * Backend de rendering, física e display.
  * Abstração semelhante ao modelo de servidores do Godot.

* **ui/**

  * Sistema de UI baseado em `Control`, containers e widgets.

---

### `game/`

Contém toda a lógica específica do jogo Forest Walk.

* **autoload/**

  * Recursos globais carregados automaticamente.
  * `Assets`: meshes, texturas e materiais.
  * `Settings`: configurações do jogo.

* **components/**

  * Componentes:

    * HeadBob
    * CameraSway
    * FlashlightSway
    * StaminaComponent

* **entities/**

  * Entidades do jogo:

    * Player
    * Árvores e elementos do ambiente.

* **levels/**

  * Cenas principais do jogo.
  * `ForestLevel` é o nível inicial.

* **ui/**

  * HUD e elementos de interface do jogador.

---

## Árvore de Nós (Scene Graph)

Exemplo simplificado da árvore do jogador:

```
Player (CharacterBody3D)
└── Head
    └── HeadBob
        └── CameraSway
            └── HeadOffset
                └── Camera3D
                    └── FlashlightSway
                        └── Flashlight (SpotLight3D)
```

### Conceito das Camadas

* **Player**: lógica de movimento, input e física.
* **Head**: ponto de rotação vertical (mouse).
* **HeadBob**: animação de caminhada/corrida.
* **CameraSway**: inclinação e balanço da câmera.
* **FlashlightSway**: movimento natural da lanterna.

Cada efeito é isolado em um Node, facilitando manutenção e ajustes finos.

---

## Fluxo de Execução

1. `main.py` inicializa a engine e cria a janela.
2. O `ForestLevel` é carregado.
3. Assets globais são inicializados via autoload.
4. O jogador é instanciado e inserido na cena.
5. Input do usuário é processado pelo `PlayerController`.
6. Componentes atualizam câmera, stamina e HUD.

---

## Instalação

### Requisitos

* Python **3.11**
* Sistema operacional: Windows

### Passos

Este projeto utiliza **uv** para gerenciamento de dependências e execução.

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd forest-walk

# Sincronize as dependências
uv sync
```

---

## Execução

```bash
python main.py
```

O jogo iniciará em tela com o jogador no centro do cenário.

### Controles Básicos

* **WASD**: mover
* **Mouse**: olhar
* **Shift**: correr

---
