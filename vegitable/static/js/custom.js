
'use strict';

$(document).ready(function(){
    var global_amount = 0;
    var counter= 1;
    var arrival_qty_list = {}
    var global_weight = 0;
    var local_amount = {};
    var local_weight = {};

    $(document).on("change", ".calculate_amount", function() {
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

    $(document).on("change", "#cooli", function() {
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

    $(document).on("change", ".add_new_sales_custom_select", function() {
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



    

    $('#add_arrivel_entry_list').click(function() {
        $('#tableWrapper')
        .children('tbody')
        .last().append(
        `
            <tr style='margin-top:3%;margin-bottom:3%;' id ="`+counter+`_child">
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Former Name' name ="`+counter+`_farmer_name" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Iteam Name' name ="`+counter+`_iteam_name" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Qty' id ="`+counter+`_qty" name ="`+counter+`_qty" class="qty_validation" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Weight' name ="`+counter+`_weight" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Lot Number' name ="`+counter+`_remark" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Advance Amount' value="0" name ="`+counter+`_advance_amount" required=''>
                    </div>
                </td>
                <td>
                    <div class='tog-top-4'>
                        <img class='close_button' src="/static/images/remove.png" name="`+counter+`"/>
                        </div>
                </td>
            </tr>
            `
        );counter=counter+1
    });


    $(document).on("keyup", ".qty_validation", function() {
        var element_name = $(this).attr("name");
        var element_value = $(this).val();
        //var arrival_qty_list = {}
        arrival_qty_list[element_name] = parseInt(element_value);

        
        var total = 0;
        for (var [key, value] of Object.entries(arrival_qty_list)) {
            if(Number.isNaN(value)){
                value= 0;
            }
            
            total = total+parseInt(value);
            
          }

        if(total==parseInt($("#total_number_of_bags").val())){
            $("#save").show();
        }else{
            $("#save").hide();
        }

    });


    $(document).on("click", ".close_button", function() {
        //Get the element name
        var element_name = $(this).attr("name");

        if($('#'+element_name+'_qty').length){
            var local_qty_element = $('#'+element_name+'_qty').attr("name");
            arrival_qty_list[local_qty_element] = 0;

            var total = 0;
            for (var [key, value] of Object.entries(arrival_qty_list)) {
                if(Number.isNaN(value)){
                    value= 0;
                }
                total = total+parseInt(value);
            }

            if(total==parseInt($("#total_number_of_bags").val())){
                $("#save").show();
            }else{
                $("#save").hide();
            }

        }else{
            alert("Element does not exists");
        }
        

        // Delete the child
        $('#'+element_name+'_child').remove();
    });
    
    $(document).on("click", "#add_sales_entry_list", function() {
    
        var iteam_goods_list = "";
        'use strict';

        $.ajax({
            url: "/get_arrival_goods_list",
            dataType: 'json',
            data:{
            },
            type: 'GET',
            async: false,
            cache: false,
            timeout: 90000,
            fail: function(){
                iteam_goods_list="";
            },
            success: function(data){ 
                iteam_goods_list = data.iteam_goods_list;
            }
        });
     

        var select_option = '<option selected="true" disabled="disabled">Choose Lot No</option>';
        for (var [key, value] of Object.entries(iteam_goods_list)) {
            select_option = select_option + "<option value='"+key+"'>"+value+"</option>";
          }
        
        $('#tableWrapper')
        .children('tbody')
        .last().append(
        `
        <tr style='margin-top:3%;margin-bottom:3%;' id ="`+counter+`_child">
        <td>
            <div class='comment-your'>
                <select class="add_new_sales_custom_select" name="`+counter+`_lot_number" id ="`+counter+`_lot_number">
                    `+select_option+`
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
                <img class='close_button' src="static/images/remove.png" onClick="removeElement('`+counter+`_child');"/>
             </div>
        </td>
    </tr>
            `
        );counter=counter+1
    });


    $(document).on("change", "#patti_entry_date", function() {
    
        var lorry_list = "";
        'use strict';

        var element_value = $(this).val();

        $.ajax({
            url: "/get_all_lorry_number/"+element_value,
            dataType: 'json',
            data:{
            },
            type: 'GET',
            async: false,
            cache: false,
            timeout: 90000,
            fail: function(){
                lorry_list="";
            },
            success: function(data){ 
                lorry_list = data.lorry_number_list;
            }
        });
     
       
        var select_option = '<option selected="true" disabled="disabled">Choose Lorry Number</option>';
        for (var index = 0; index < lorry_list.length; index++) {
            select_option = select_option + "<option value='"+lorry_list[index]+"'>"+lorry_list[index]+"</option>";
            console.log(lorry_list[index]);
        }

    
        $('#patti_lorry_number').children("option").remove();
        $('#patti_lorry_number').append(select_option);

    });

    $(document).on("change", "#patti_lorry_number", function() {
    
        var patti_farmer_list = "";
        'use strict';

        var lorry_number_value = $(this).val();
        var patti_date_value = $('#patti_entry_date').val();

        $.ajax({
            url: "/get_all_farmer_name",
            dataType: 'json',
            data:{
                'lorry_number':lorry_number_value,
                'patti_date':patti_date_value
            },
            type: 'GET',
            async: false,
            cache: false,
            timeout: 90000,
            fail: function(){
                patti_farmer_list="";
            },
            success: function(data){ 
                patti_farmer_list = data.farmer_list;
            }
        });
     
       
        var select_option = '<option selected="true" disabled="disabled">Choose Farmer Name</option>';
        for (var index = 0; index < patti_farmer_list.length; index++) {
            select_option = select_option + "<option value='"+patti_farmer_list[index]+"'>"+patti_farmer_list[index]+"</option>";
            console.log(patti_farmer_list[index]);
        }

    
        $('#patti_farmer_namer').children("option").remove();
        $('#patti_farmer_namer').append(select_option);

    });



    $(document).on("change", "#patti_farmer_namer", function() {
        
        var farmer_advance = 0;
        var patti_sales_entry_list = "";

        var patti_farmer_name_value = $(this).val();
        
        var patti_date_value = $('#patti_entry_date').val();

        var patti_lorry_value = $('#patti_lorry_number').val();

        $.ajax({
            url: "/get_sales_list_for_arrival_iteam_list",
            dataType: 'json',
            data:{
                'patti_farmer':patti_farmer_name_value,
                'patti_date':patti_date_value,
                'patti_lorry':patti_lorry_value
            },
            type: 'GET',
            async: false,
            cache: false,
            timeout: 90000,
            fail: function(){
                farmer_advance= 0;
                patti_sales_entry_list="";
            },
            success: function(data){ 
                patti_sales_entry_list = data.sales_goods_list;
                farmer_advance = data.farmer_advance;
            }
        });

        $('#advance_amount').val(farmer_advance);

        for (var index = 0; index < patti_sales_entry_list.length; index++) {
            console.log(patti_sales_entry_list[index]['iteam_name']);
            console.log(patti_sales_entry_list[index]['net_weight']);
            console.log(patti_sales_entry_list[index]['lot_number']);
            
                $('#tableWrapper')
                    .children('tbody')
                    .last().append(
                    `
                    <tr style='margin-top:3%;margin-bottom:3%;' id ="`+counter+`_child">
                                    <td>
                                        <div class='comment-your'>
                                            <input type='text' placeholder='Iteam Name' name ="`+counter+`_iteam_name" id="`+counter+`_iteam_name" value="`+patti_sales_entry_list[index]['iteam_name']+`" required='' readonly>
                                            
                                        </div>
                                    </td>

                                    <td>
                                        <div class='comment-your'>
                                            <input type='text' placeholder='Iteam Name' name ="`+counter+`_lot_number" id="`+counter+`_lot_number" value="`+patti_sales_entry_list[index]['lot_number']+`" required='' readonly>
                                        </div>
                                    </td>
                                    
                                    <td>
                                        <div class='comment-your'>
                                            <input type='text' placeholder='Weight' name ="`+counter+`_weight" id ="`+counter+`_weight" value="`+patti_sales_entry_list[index]['net_weight']+`" required=''>
                                        </div>
                                    </td>
                                    <td>
                                        <div class='comment-your'>
                                            <input type='text' placeholder='Rate' class="patti_rate" name ="`+counter+`_rate" id="`+counter+`_rate" required=''>
                                        </div>
                                    </td>
                                    <td>
                                        <div class='comment-your'>
                                            <input type='text' placeholder='Amount' name ="`+counter+`_amount" required='' id= "`+counter+`_amount">
                                        </div>
                                    </td>
                                </tr>
                                `
                    );counter=counter+1
                
              
        }

    });


    $(document).on("change", ".patti_rate", function() {
        var rate_id = $(this).attr("id");
        var rate_value = $(this).val();
        
        var res = rate_id.split("_");

        var netweigth = $(`#`+res[0]+`_weight`).val();
        var amount  = ((rate_value*2)*netweigth)/100;
        $(`#`+res[0]+`_amount`).val(amount);

        local_amount[`#`+res[0]+`_amount`] = amount;
        
        local_weight[`#`+res[0]+`_weight`] = netweigth;

        global_amount = 0;
        for (var [key, value] of Object.entries(local_amount)) {
            global_amount = parseFloat(global_amount) + parseFloat(value);
        }

        global_weight = 0;
        for (var [key, value] of Object.entries(local_weight)) {
            global_weight = parseFloat(global_weight) + parseFloat(value);        }

        var advance_amount = $('#advance_amount').val();
        var hamali = $('#hamali').val();

        $('#total_weight').val(global_weight);
        $('#net_amount').val(global_amount-parseFloat(advance_amount)-parseFloat(hamali));

    });

    $(document).on("change", "#hamali", function() {

        global_amount = 0;
        for (var [key, value] of Object.entries(local_amount)) {
            global_amount = parseFloat(global_amount) + parseFloat(value);
        }

        global_weight = 0;
        for (var [key, value] of Object.entries(local_weight)) {
            global_weight = parseFloat(global_weight) + parseFloat(value);        }

        var advance_amount = $('#advance_amount').val();
        var hamali = $('#hamali').val();

        $('#total_weight').val(global_weight);
        $('#net_amount').val(global_amount-parseFloat(advance_amount)-parseFloat(hamali));

    });

    


});

function removeElement(el) {

    console.log(el);

    var element = document.getElementById(el);

    element.remove();
}

