from utils.namespace import Namespace


# solver states
STATE = Namespace(
    UNINITIALIZED="uninitialized",
    INITIALIZED="initialized",
    BOOTSTRAPPED="bootstrapped",
    RUNNING="running",
    PAUSED="paused",
    FINISHED="finished",
    SOLVING="solving")

# transition symbols
ACTION = Namespace(
    INIT="init",
    RUN="run",
    PAUSE="pause",
    FINISH="finish",
    RESET="reset",
    SOLVE="solve")

# transition mapping
TRANSITIONS = {
    STATE.UNINITIALIZED: {
        ACTION.RESET:  STATE.UNINITIALIZED,
        ACTION.INIT:   STATE.INITIALIZED,
        ACTION.SOLVE:  STATE.SOLVING},
    STATE.INITIALIZED: {
        ACTION.RESET:  STATE.UNINITIALIZED,
        ACTION.RUN:    STATE.BOOTSTRAPPED},
    STATE.BOOTSTRAPPED: {
        ACTION.RUN:    STATE.RUNNING,
        ACTION.PAUSE:  STATE.PAUSED,
        ACTION.FINISH: STATE.FINISHED},
    STATE.RUNNING: {
        ACTION.PAUSE:  STATE.PAUSED,
        ACTION.FINISH: STATE.FINISHED},
    STATE.PAUSED: {
        ACTION.RESET:  STATE.UNINITIALIZED,
        ACTION.RUN:    STATE.RUNNING,
        ACTION.PAUSE:  None,
        ACTION.FINISH: STATE.FINISHED},
    STATE.FINISHED: {
        ACTION.RESET:  STATE.UNINITIALIZED,
        ACTION.PAUSE:  None,
        ACTION.FINISH: None},
    STATE.SOLVING: {
        ACTION.INIT:   STATE.INITIALIZED}}
