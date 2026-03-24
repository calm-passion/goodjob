import { a6 } from "./aaa"

function main() {
    a5()
    a1()
    function a5() {
        a2()
    }
    a6()
}

export function a1() {
    a1()
    a2()
    a3()
}
function a2() {
    a3()
    a4()
}
function a3() {
    a4()
}
function a4() {
    a2()
}
