
$(document).ready(function(){
    var global_amount = 0;
    $('.calculate_amount').change(function (){
        var rate_id = $(this).attr("id");
        var rate_value = $(this).val();

        var res = rate_id.split("_");
        var net_weight = `#`+res[0]+`_net_weight`;
        var net_weight_value = $(net_weight).val();

        var amount = ((rate_value*2)*net_weight_value)/100;

        $(`#`+res[0]+`_amount`).val(amount);
        global_amount = global_amount+amount;

        $('#rmc').val(global_amount*0.006);
        $('#comission').val(global_amount*0.05);
        var rmc_value = $('#rmc').val();
        var comission_value = $('#comission').val();
        var cooli_value = $('#cooli').val();
        if(cooli_value.length<=0){
            cooli_value = 0;
        }
        

        var final_value = parseFloat(rmc_value)+parseFloat(comission_value)+parseFloat(cooli_value)+parseFloat(global_amount);
        $('#total_amount').val(final_value);
        
    });

    $('#cooli').change(function (){
        $('#rmc').val(global_amount*0.006);
        $('#comission').val(global_amount*0.05);
        var rmc_value = $('#rmc').val();
        var comission_value = $('#comission').val();
        var cooli_value = $('#cooli').val();
        if(cooli_value.length<=0){
            cooli_value = 0;
        }
        

        var final_value = parseFloat(rmc_value)+parseFloat(comission_value)+parseFloat(cooli_value)+parseFloat(global_amount);
        $('#total_amount').val(final_value);
    });


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

    $('#add_sales_entry_list').click(function() {
        $('#tableWrapper')
        .children('tbody')
        .last().append(
        `
        <tr style='margin-top:3%;margin-bottom:3%;' id ="`+counter+`_child">
        <td>
            <div class='comment-your'>
                <select class="custom-select" name="`+counter+`_lot_number" id ="`+counter+`_lot_number">
                    {% for arrival_detail in arrival_goods_detail%}
                    <option value="{{arrival_detail.remarks}}">{{arrival_detail.remarks}}</option>
                    {%endfor%}
                </select>
                
            </div>
        </td>

        <td>
            <div class='comment-your'>
                <input type='text' placeholder='Iteam Name' name ="`+counter+`_iteam_name" id="`+counter+`_iteam_name" required='' readonly>
            </div>
        </td>
        
        <td>
            <div class='comment-your'>
                <input type='text' placeholder='Bags' name ="`+counter+`_bags" required=''>
            </div>
        </td>
        <td>
            <div class='comment-your'>
                <input type='text' placeholder='Net Weigth' name ="`+counter+`_net_weight" id="`+counter+`_net_weight" required=''>
            </div>
        </td>
        <td>
            <div class='comment-your'>
                <input type='text' placeholder='Rates' name ="`+counter+`_rates" required='' id= "`+counter+`_rates" class="calculate_amount">
            </div>
        </td>
        <td>
            <div class='comment-your'>
                <input type='text' placeholder='Amount' name ="`+counter+`_amount" id= "`+counter+`_amount" required='' readonly>
            </div>
        </td>
        <td>
            <div class='tog-top-4'>
                <img class='close_button' src="static/images/remove.png" onClick="removeElement(`+counter+`_child');"/>
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

