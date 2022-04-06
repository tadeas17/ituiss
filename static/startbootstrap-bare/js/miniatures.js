
import "../../jquery-3.6.0";

var_selected_id = -1

function miniature_click(miniature_id)
{
    
    var element;
    if (miniature_id != -1)
        element = document.getElementById(miniature_id);
    else
        element = document.getElementById("row_new");

    var former_element;
    if (miniature_id != 1)
        former_element = document.getElementById(var_selected_id);
    else
        former_element = document.getElementById("row_new");
    
    former_element.removeAttribute("style");
    element.setAttribute("style", "background-color: gray;");
}