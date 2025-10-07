import logging
from typing import Any, Dict
from typing_extensions import Never
from agent_framework import WorkflowBuilder, Case, Default, WorkflowViz, WorkflowContext, executor
from src.models.request_models import RouterOutputModel

import json  # Add this import for optional JSON formatting if you want to include metadata

logger = logging.getLogger(__name__)


def create_workflow_executors(
    router_service,
    it_diagnose_service,
    it_resolve_service,
    hr_service,
):
    """
    Crea todos los executors del workflow usando el decorador @executor.
    Retorna un diccionario con todos los executors para usar en el builder.
    
    IMPORTANTE: Los executors deben definirse dentro de una función para tener
    acceso a los servicios mediante closure.
    """
    
    # ========== EXECUTOR INICIAL: ALMACENAR INPUT ==========
    
    @executor(id="store_user_input")
    async def store_user_input(user_input: str, ctx: WorkflowContext[str]) -> None:
        """
        Nodo inicial: almacena el input del usuario y lo pasa al clasificador.
        """
        logger.info(f"📥 Almacenando input del usuario: {user_input[:50]}...")
        # Pasar el input original al siguiente nodo
        await ctx.send_message(user_input)
    
    # ========== EXECUTOR: CLASIFICAR REQUEST ==========
    
    @executor(id="classify_request")
    async def classify_request(user_input: str, ctx: WorkflowContext[Dict[str, Any]]) -> None:
        """
        Nodo: ejecuta el RouterAgent para clasificar el tipo de consulta.
        """
        logger.info("🔍 Clasificando tipo de consulta...")
        
        classification: RouterOutputModel = await router_service.classify(user_input)
        
        # Crear contexto con la información de clasificación
        context_data = {
            "original_input": user_input,
            "tipo": classification.tipo,
            "confidence": classification.confidence,
            "details": classification.details
        }
        
        logger.info(
            f"✅ Clasificación: tipo={classification.tipo}, "
            f"confidence={classification.confidence:.2f}"
        )
        
        # Enviar el contexto al switch
        await ctx.send_message(context_data)
    
    # ========== FUNCIÓN PARA EL SWITCH ==========
    @executor(id="extract_type")
    async def extract_type(context_data: Dict[str, Any], ctx: WorkflowContext[Dict[str, Any]]) -> None:
        """
        Executor intermedio que extrae el tipo y pasa el contexto al switch.
        """
        tipo = context_data.get("tipo", "other")
        logger.debug(f"📊 Tipo extraído para switch: {tipo}")
        await ctx.send_message(context_data)
    
    # ========== RAMA IT: DIAGNÓSTICO ==========
    
    @executor(id="it_diagnose_executor")
    async def it_diagnose_executor(context_data: Dict[str, Any], ctx: WorkflowContext[Dict[str, Any]]) -> None:
        """
        Nodo IT #1: diagnóstico técnico del problema.
        """
        user_input = context_data.get("original_input", "")
        logger.info("🔧 Ejecutando diagnóstico técnico...")
        
        diagnostic = await it_diagnose_service.diagnose(user_input)
        
        # Agregar diagnóstico al contexto
        context_data["it_diagnostic"] = diagnostic
        
        logger.info(f"📋 Diagnóstico generado: {diagnostic[:100]}...")
        
        # Pasar al siguiente nodo de la rama IT
        await ctx.send_message(context_data)
    
    # ========== RAMA IT: RESOLUCIÓN ==========
    
    @executor(id="it_resolve_executor")
    async def it_resolve_executor(context_data: Dict[str, Any], ctx: WorkflowContext[Never, Dict[str, Any]]) -> None:
        """
        Nodo IT #2: propone solución basada en el diagnóstico.
        Este es el nodo final de la rama IT.
        """
        diagnostic = context_data.get("it_diagnostic", "")
        user_input = context_data.get("original_input", "")
        logger.info("🛠️ Generando solución técnica...")
        
        solution = await it_resolve_service.resolve(diagnostic, user_input)
        
        # Preparar respuesta final (mantén el dict internamente si necesitas logs)
        final_result = {
            "final_response": solution,
            "response_type": "it_solution",
            "tipo": context_data.get("tipo"),
            "confidence": context_data.get("confidence")
        }
        
        logger.info(f"✅ Solución generada: {solution[:100]}...")
        
        # Yield solo la respuesta principal como string para DevUI
        # Si quieres incluir metadata, usa: json.dumps(final_result, indent=2)
        await ctx.yield_output(solution)  # Cambiado de final_result a solution
    
    # ========== RAMA HR ==========
    
    @executor(id="hr_executor")
    async def hr_executor(context_data: Dict[str, Any], ctx: WorkflowContext[Never, Dict[str, Any]]) -> None:
        """
        Nodo HR: maneja consultas de recursos humanos.
        Este es el nodo final de la rama HR.
        """
        user_input = context_data.get("original_input", "")
        logger.info("👥 Procesando consulta de RRHH...")
        
        hr_response = await hr_service.handle(user_input)
        
        # Preparar respuesta final (mantén el dict internamente si necesitas logs)
        final_result = {
            "final_response": hr_response,
            "response_type": "hr_response",
            "tipo": context_data.get("tipo"),
            "confidence": context_data.get("confidence")
        }
        
        logger.info(f"✅ Respuesta RRHH generada: {hr_response[:100]}...")
        
        # Yield solo la respuesta principal como string para DevUI
        # Si quieres incluir metadata, usa: json.dumps(final_result, indent=2)
        await ctx.yield_output(hr_response)  # Cambiado de final_result a hr_response
    
    # ========== RAMA OTHER (FALLBACK) ==========
    
    @executor(id="generic_message_executor")
    async def generic_message_executor(context_data: Dict[str, Any], ctx: WorkflowContext[Never, Dict[str, Any]]) -> None:
        """
        Nodo genérico: mensaje estándar cuando no se reconoce el tipo.
        Este NO es un agente, solo devuelve un mensaje fijo.
        """
        logger.info("💬 Generando respuesta genérica...")
        
        generic_msg = (
            "Lo siento, no pude clasificar tu consulta de manera precisa. "
            "Por favor, reformula tu pregunta o contacta directamente con "
            "el departamento correspondiente (IT o RRHH)."
        )
        
        # Preparar respuesta final (mantén el dict internamente si necesitas logs)
        final_result = {
            "final_response": generic_msg,
            "response_type": "generic",
            "tipo": context_data.get("tipo", "other"),
            "confidence": context_data.get("confidence", 0.0)
        }
        
        logger.info("✅ Respuesta genérica devuelta")
        
        # Yield solo la respuesta principal como string para DevUI
        # Si quieres incluir metadata, usa: json.dumps(final_result, indent=2)
        await ctx.yield_output(generic_msg)  # Cambiado de final_result a generic_msg
    
    # Retornar todos los executors
    return {
        "store_user_input": store_user_input,
        "classify_request": classify_request,
        "extract_type": extract_type,
        "it_diagnose_executor": it_diagnose_executor,
        "it_resolve_executor": it_resolve_executor,
        "hr_executor": hr_executor,
        "generic_message_executor": generic_message_executor,
    }


def build_support_workflow(executors: Dict[str, Any]):
    """
    Construye el workflow usando los executors creados.
    
    Args:
        executors: Diccionario con todos los executors del workflow
        
    Returns:
        Workflow construido y listo para ejecutar
    """
    logger.info("🏗️ Construyendo workflow con branching logic...")
    
    workflow = (
        WorkflowBuilder()
        # Nodo inicial
        .set_start_executor(executors["store_user_input"])
        
        # Edge al clasificador
        .add_edge(executors["store_user_input"], executors["classify_request"])
        
        # CRÍTICO: Conectar el clasificador al switch
        # El switch debe ir DESPUÉS de classify_request
        .add_edge(executors["classify_request"], executors["extract_type"])
        
        # Switch-case branching logic
        # La condición debe ser una función que reciba el context_data
        .add_switch_case_edge_group(
            executors["extract_type"],
            [
                # Caso 1: Consulta técnica (IT) - rama secuencial
                Case(
                    condition=lambda context_data: context_data.get("tipo") == "it",
                    target=executors["it_diagnose_executor"]
                ),
                
                # Caso 2: Consulta de recursos humanos
                Case(
                    condition=lambda context_data: context_data.get("tipo") == "hr",
                    target=executors["hr_executor"]
                ),
                
                # Caso default: consultas no clasificadas
                Default(target=executors["generic_message_executor"]),
            ],
        )
        
        # Rama IT: flujo secuencial (diagnóstico → solución)
        .add_edge(executors["it_diagnose_executor"], executors["it_resolve_executor"])
        
        .build()
    )
    
    logger.info("✅ Workflow construido exitosamente")
    return workflow


def visualize_workflow(workflow):
    """
    Genera y muestra visualizaciones del workflow construido.
    
    Args:
        workflow: El workflow construido con WorkflowBuilder
    """
    logger.info("📊 Generando visualizaciones del workflow...")
    
    try:
        viz = WorkflowViz(workflow)
        
        # ========== 1. DIAGRAMA MERMAID (texto) ==========
        logger.info("\n" + "="*70)
        logger.info("📈 DIAGRAMA MERMAID DEL WORKFLOW (copiar a docs/markdown):")
        logger.info("="*70)
        mermaid_content = viz.to_mermaid()
        print(mermaid_content)
        logger.info("="*70 + "\n")
        
        # Guardar Mermaid en archivo de texto
        try:
            with open("images/workflow_diagram.mmd", "w", encoding="utf-8") as f:
                f.write(mermaid_content)
            logger.info("✅ Diagrama Mermaid guardado en: images/workflow_diagram.mmd")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo guardar archivo Mermaid: {e}")
        
        # ========== 2. DIAGRAMA DOT (GraphViz) ==========
        logger.info("\n" + "="*70)
        logger.info("🔷 DIAGRAMA DOT (GraphViz format):")
        logger.info("="*70)
        dot_content = viz.to_digraph()
        print(dot_content)
        logger.info("="*70 + "\n")
        
        # Guardar DOT en archivo
        try:
            with open("images/workflow_diagram.dot", "w", encoding="utf-8") as f:
                f.write(dot_content)
            logger.info("✅ Diagrama DOT guardado en: images/workflow_diagram.dot")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo guardar archivo DOT: {e}")
        
        # ========== 3. EXPORTAR IMÁGENES (requiere graphviz) ==========
        logger.info("\n📸 Intentando exportar imágenes del workflow...")
        
        try:
            # SVG (recomendado - formato vectorial)
            svg_file = viz.save_svg("images/workflow_diagram.svg")
            logger.info(f"✅ Diagrama SVG exportado a: {svg_file}")
            
            # PNG (formato raster)
            png_file = viz.save_png("images/workflow_diagram.png")
            logger.info(f"✅ Diagrama PNG exportado a: {png_file}")
            
            # PDF (formato vectorial para imprimir)
            pdf_file = viz.save_pdf("images/workflow_diagram.pdf")
            logger.info(f"✅ Diagrama PDF exportado a: {pdf_file}")
            
            logger.info("\n🎉 Visualizaciones exportadas exitosamente!")
            
        except ImportError:
            logger.warning("\n⚠️ No se pudieron exportar imágenes.")
            logger.info("💡 Para exportar SVG/PNG/PDF, instala:")
            logger.info("   pip install agent-framework[viz]")
            logger.info("\n💡 También necesitas instalar GraphViz binaries:")
            logger.info("   - macOS:   brew install graphviz")
            logger.info("   - Linux:   sudo apt-get install graphviz")
            logger.info("   - Windows: https://graphviz.org/download/")
        except Exception as e:
            logger.warning(f"⚠️ Error al exportar imágenes: {e}")
        
        # ========== 4. ANÁLISIS DEL WORKFLOW ==========
        logger.info("\n📋 ANÁLISIS DE COMPLEJIDAD DEL WORKFLOW:")
        edge_count = dot_content.count(" -> ")
        node_count = dot_content.count('[label=')
        logger.info(f"   • Nodos (executors): {node_count}")
        logger.info(f"   • Conexiones (edges): {edge_count}")
        logger.info(f"   • Ramas del switch: 3 (IT, HR, Other)")
        logger.info(f"   • Flujo secuencial IT: 2 agentes encadenados\n")
        
    except Exception as e:
        logger.error(f"❌ Error al generar visualizaciones: {e}")
        import traceback
        traceback.print_exc()


# ========== FUNCIÓN PRINCIPAL ==========

def create_support_workflow(
    router_service,
    it_diagnose_service,
    it_resolve_service,
    hr_service,
    visualize: bool = False,
):
    """
    Factory function para crear el workflow de soporte completo.
    
    Args:
        router_service: Servicio de clasificación (RouterAgentService)
        it_diagnose_service: Servicio de diagnóstico IT
        it_resolve_service: Servicio de resolución IT
        hr_service: Servicio de RRHH
        visualize: Si True, genera y guarda visualizaciones del workflow
    
    Returns:
        Workflow configurado y listo para ejecutar
        
    Ejemplo de uso:
        workflow = create_support_workflow(
            router_service, it_diag, it_res, hr,
            visualize=True
        )
        
        # Ejecutar con streaming
        async for event in workflow.run_stream("Mi problema es..."):
            print(event)
    """
    # Crear todos los executors con los servicios
    executors = create_workflow_executors(
        router_service=router_service,
        it_diagnose_service=it_diagnose_service,
        it_resolve_service=it_resolve_service,
        hr_service=hr_service,
    )
    
    # Construir el workflow
    workflow = build_support_workflow(executors)
    
    # Generar visualizaciones si se solicita
    if visualize:
        visualize_workflow(workflow)
    
    return workflow