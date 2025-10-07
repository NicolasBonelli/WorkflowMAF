
import asyncio
import logging
from config.config import AZURE_AI_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME, AZURE_OPENAI_API_KEY

from src.services.llm_client import LLMClientWrapper
from src.agents.triage_agent import RouterAgentService
from src.agents.it_diagnose_agent import ITDiagnoseService
from src.agents.it_resolve_agent import ITResolveService
from src.agents.hr_agent import HRAgentService
from src.workflows.workflow_builder import create_support_workflow

# Import DevUI para visualización
from agent_framework import WorkflowViz,WorkflowOutputEvent
from agent_framework.devui import serve

logger = logging.getLogger(__name__)


async def run_test_queries_streaming(workflow, test_queries=None):
    """Ejecuta una lista de consultas usando workflow.run_stream y muestra eventos/resultado."""
    if test_queries is None:
        test_queries = [
            "No puedo acceder al servidor de producción, me da error 500",
            "¿Cuántos días de vacaciones me corresponden este año?",
            "¿Cuál es el sentido de la vida?"
        ]
    for query in test_queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"📝 Query (streaming): {query}")
        logger.info(f"{'='*60}")

        final_output = None

        async for event in workflow.run_stream(query):
            logger.debug(f"Evento recibido: {event}")
            try:
                if isinstance(event, WorkflowOutputEvent):
                    final_output = event.data
                    logger.info("🔚 Evento final recibido (WorkflowOutputEvent)")
                else:
                    evt_data = getattr(event, 'data', None)
                    if evt_data is not None:
                        logger.info(f"Evento intermedio con data: {evt_data}")
                    else:
                        logger.info(f"Evento: {event}")
            except Exception:
                logger.info(f"Evento (inspección fallida): {event}")

        # Mostrar resultado final
        print("Resultado del workflow (stream):")
        if final_output is None:
            print("(No se recibió WorkflowOutputEvent; puede que la salida esté en eventos intermedios)")
        else:
            if isinstance(final_output, dict):
                final_resp = final_output.get('final_response')
                if final_resp is not None:
                    print('\n--- Respuesta principal (final_response) ---')
                    print(final_resp)
                    print('--- Fin de respuesta principal ---\n')

                other = {k: v for k, v in final_output.items() if k != 'final_response'}
                if other:
                    try:
                        from pprint import pprint
                        print('Otros campos de la salida:')
                        pprint(other)
                    except Exception:
                        print('Otros campos:', other)
            else:
                print(str(final_output))


async def run_server(run_tests: bool = False, test_queries=None):
    """
    Inicializa todos los servicios y agentes, construye el workflow
    y levanta el servidor DevUI para visualización interactiva.
    """
    logger.info("🚀 Iniciando servidor de workflow...")
    
    # ========== 1. Inicializar cliente LLM ==========
    logger.info("🔧 Configurando cliente Azure OpenAI...")
    llm_wrapper = LLMClientWrapper(
        endpoint=AZURE_AI_PROJECT_ENDPOINT,
        deployment_name=AZURE_AI_MODEL_DEPLOYMENT_NAME,
        api_key=AZURE_OPENAI_API_KEY
    )
    
    # ========== 2. Crear agentes con instrucciones específicas ==========
    logger.info("🤖 Creando agentes...")
    
    # Agente clasificador (Router)
    router_agent = await llm_wrapper.create_chat_agent(
        instructions=(
            "Eres un clasificador de consultas empresariales. "
            "Analiza el mensaje del usuario y determina si es una consulta técnica (IT), "
            "de recursos humanos (HR) o de otro tipo. "
            "Responde SIEMPRE en formato JSON con los campos: "
            "tipo (it|hr|other), confidence (0-1) y details (breve explicación). "
            "Ejemplo: {\"tipo\":\"it\",\"confidence\":0.95,\"details\":\"problema de acceso al servidor\"}"
        ),
        name="RouterAgent"
    )
    
    # Agente de diagnóstico IT
    it_diagnose_agent = await llm_wrapper.create_chat_agent(
        instructions=(
            "Eres un especialista técnico en diagnóstico de problemas IT. "
            "Tu trabajo es analizar problemas técnicos y describir la posible causa raíz. "
            "Menciona qué logs, datos o información adicional serían necesarios para investigar. "
            "Sé conciso pero preciso en tu análisis."
        ),
        name="ITDiagnoseAgent"
    )
    
    # Agente de resolución IT
    it_resolve_agent = await llm_wrapper.create_chat_agent(
        instructions=(
            "Eres un especialista técnico en resolución de problemas IT. "
            "Basándote en el diagnóstico previo, proporciona pasos concretos y seguros "
            "para resolver el problema. Genera una lista numerada de acciones claras. "
            "Prioriza soluciones que no comprometan la seguridad o estabilidad del sistema."
        ),
        name="ITResolveAgent"
    )
    
    # Agente de recursos humanos
    hr_agent = await llm_wrapper.create_chat_agent(
        instructions=(
            "Eres un asistente profesional de Recursos Humanos. "
            "Responde de forma breve, clara y profesional a consultas sobre: "
            "vacaciones, permisos, beneficios, políticas laborales, contratos, sueldos, etc. "
            "Mantén un tono cordial pero formal."
        ),
        name="HRAgent"
    )
    
    # ========== 3. Crear servicios que envuelven los agentes ==========
    logger.info("⚙️ Inicializando servicios...")
    
    router_service = RouterAgentService(router_agent)
    it_diagnose_service = ITDiagnoseService(it_diagnose_agent)
    it_resolve_service = ITResolveService(it_resolve_agent)
    hr_service = HRAgentService(hr_agent)
    
    # ========== 4. Construir el workflow completo ==========
    logger.info("🏗️ Construyendo workflow con branching logic...")
    
    workflow = create_support_workflow(
        router_service=router_service,
        it_diagnose_service=it_diagnose_service,
        it_resolve_service=it_resolve_service,
        hr_service=hr_service
    )
    
    logger.info("✅ Workflow construido exitosamente")
    
    # ========== 5. Levantar DevUI server para visualización ==========
    logger.info("🌐 Levantando servidor DevUI...")
    logger.info("📊 Podrás visualizar y testear el workflow en el navegador")
    # Si run_tests está activado, ejecutamos los tests en streaming y salimos
    if run_tests:
        await run_test_queries_streaming(workflow, test_queries)
        return
        

    return workflow


if __name__ == "__main__":
    import sys

    # Si se pasa 'test' como argumento, ejecutamos las pruebas en streaming
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Puedes pasar queries adicionales como argumentos siguientes
        custom_queries = sys.argv[2:] if len(sys.argv) > 2 else None
        asyncio.run(run_server(run_tests=True, test_queries=custom_queries))
    else:
        workflow=asyncio.run(run_server())
        serve(entities=[workflow], auto_open=True)
