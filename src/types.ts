/**
 * 函数调用图的 JSON 节点结构（最终输出格式）
 */
export interface GraphNode {
  function_name: string;
  definition_file_path: string;
  /** 格式：startLine_endLine（1-based 行号） */
  location: string;

  
  childs: GraphNode[] | null;
}
