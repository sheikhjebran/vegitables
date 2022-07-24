
$(document).ready(function(){
    
    $('.custom-select').change(function () {
        var lot_number_Id = $(this).attr("id");
        var selected_lot = $(this).val();
        
        var res = lot_number_Id.split("_");
        var iteam_name = `#`+res[0]+`_iteam_name`;

        $.ajax({
            url: "/get_arrival_goods_iteam_name",
            dataType: 'json',
            data:{
                "selected_lot": selected_lot
            },
            type:'GET',
            success: function (data) {
                $(iteam_name).val(data.iteam_name_list);
        },
            error: function(){
                console.log("error");
                }        
            });

    });



        var counter= 1;
    $('#add_arrivel_entry_list').click(function() {
        $('#tableWrapper')
        .children('tbody')
        .last().append(
        `
            <tr style='margin-top:3%;margin-bottom:3%;' id ="`+counter+`_child">
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Former Name' name ="`+counter+`_name" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Iteam Name' name ="`+counter+`_iteam_name" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Qty' name ="`+counter+`_qty" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Weight' name ="`+counter+`_weight" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Remark' name ="`+counter+`_remark" required=''>
                    </div>
                </td>
                <td>
                    <div class='tog-top-4'>
                        <img class='close_button' src="{% static 'images/remove.png' %}" onClick="removeElement('`+counter+`_child');" '/>
                        </div>
                </td>
            </tr>
            `
        );counter=counter+1
    });

});

function removeElement(el) {
    console.log(el)
    var element = document.getElementById(el);

    element.remove();
}

