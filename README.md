# goodjob

这是一个充满无限可能的项目

我需要你给我洗一个终端插件用ts语言。这个插件是用来构建需要分析的项目的函数调用流程图。使用到的技术有ast+lsp。
ast负责定位，lsp负责跳转。
例如我再终端输入 function_graph -entry="./src/index.ts" -output="./outupt/graph.json"
function_graph是启动对于程序的指令
-entry表示需要分析的项目的入口文件的相对路径

-output表示输出的文件相对路径

函数调用流程图以函数为节点，当一个函数被多个函数调用的时候，那么这个函数只需要分析一次就好，ast中的函数节点对象可以用来做判断如果是相同的对象那么就是同一个函数。

json中每个函数节点记录的信息如下：
{

function_name:string,

definition_file_path:sting

location:start_line_number_end_line_number

childs:{}|null

}

项目支持热加载：npm run dev (可以实现热加载)
