"""Utilizacao do simulador para balanceamento de linhas de producao (projecto FIT4U).

DETALHES DO MODELO
    - 10 trabalhadores
    - 3 linhas (corte, costura, montagem)
        - 1 hora de "setup time", i.e. sempre que se inicia uma encomenda nas linhas
    - Mesas de trabalho (cenario 3 apenas)
        - nao tem tempos de setup
        - trabalhadores rendem menos que nas linhas
    - 10 produtos
        - cada produto tem um valor de complexidade entre 0.5 e 2.0 para cada linha
    - 100 encomendas
        - produto escolhido aleatoriamente
        - diferentes quantidades encomendadas
    - unidade de tempo de simulacao: hora

THROUGHPUT
    - seccoes
        1 pessoa  (100) --> 100 unidades/dia
        2 pessoas  (80) --> 180 unidades/dia
        3 pessoas  (60) --> 240 unidades/dia
        4 pessoas  (40) --> 280 unidades/dia
        5 pessoas  (20) --> 300 unidades/dia
        6 ou mais pessoas (0) --> 300 unidades/dia
    - mesas de trabalho
        30 unidades/dia por pessoa
    
CENARIOS SIMULADOS
    O objectivo e estudar o makespan se:
        Cenario 1) as seccoes tiverem um numero fixo de pessoas a trabalhar
        Cenario 2) se se puder movimentar pessoas entre linhas
        Cenario 3) se houver uma mesa de producao em que alguns trabalhadores  
                   podem fazer os sapatos do principio ao fim
"""
from components import Fit4U, AssemblyLine, WorkBench, Balancer, Dispatcher
from params import orders, changeover, setup

# ---------------------------------------------------------
# Scenario 1 ----------------------------------------------
sim1 = Fit4U("fit4u-1", orders=orders)
sim1.stack.trace = False
sim1["cut"]  = AssemblyLine(initial_workers=4,  
                            changeover=changeover["cut"], setup=setup["cut"])
sim1["sew"]  = AssemblyLine(initial_workers=3,  
                            changeover=changeover["sew"], setup=setup["sew"])
sim1["assy"] = AssemblyLine(initial_workers=3,  
                            changeover=changeover["assy"], setup=setup["assy"])
# ---------------------------------------------------------
# Scenario 2 ----------------------------------------------
sim2 = Fit4U("fit4u-2", orders=orders)
sim2.stack.trace = False
sim2["cut"]  = AssemblyLine(initial_workers=4, min_workers=1,   
                            changeover=changeover["cut"], setup=setup["cut"])
sim2["sew"]  = AssemblyLine(initial_workers=3, min_workers=1, 
                            changeover=changeover["sew"], setup=setup["sew"])
sim2["assy"] = AssemblyLine(initial_workers=3, min_workers=1, 
                            changeover=changeover["assy"], setup=setup["assy"])
sim2["balancer"] = Balancer(targets=["cut", "sew", "assy"], update_interval=0.1)
# ---------------------------------------------------------
# Scenario 3 ----------------------------------------------
sim3 = Fit4U("fit4u-3", orders=orders)
sim3.stack.trace = False
sim3["cut"]  = AssemblyLine(initial_workers=4, min_workers=1,   
                            changeover=changeover["cut"], setup=setup["cut"])
sim3["sew"]  = AssemblyLine(initial_workers=3, min_workers=1, 
                            changeover=changeover["sew"], setup=setup["sew"])
sim3["assy"] = AssemblyLine(initial_workers=3, min_workers=1, 
                            changeover=changeover["assy"], setup=setup["assy"])
sim3["bench"] = WorkBench(initial_workers=0, min_workers=0)
sim3["balancer"] = Balancer(targets=["cut", "sew", "assy", "bench"], update_interval=0.1)
sim3["dispatcher"] = Dispatcher(update_interval=1.0)

if __name__ == "__main__":
    for sim in (sim1, sim2, sim3):
        sim.single_run(seed=0)
        