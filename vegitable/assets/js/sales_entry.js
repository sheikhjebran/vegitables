"use strict";

$(document).ready(function () {

    //Sales entry variable
    const rates_input_boxs = $(".calculate_amount");
    const rmc_input_box = $("#rmc");
    const commission_input_box = $("#comission");
    const cooli_input_box = $("#cooli");
    const total_amount = $("#total_amount");

    //local variable
    var global_amount = 0;

    //logic to calculate rmc , commision, cooli
    rates_input_boxs.on("keyup change",Calculate_Rmc_Commission_Cooli);



    function Calculate_Rmc_Commission_Cooli(){
        var rate_id = $(this).attr("id");
        var rate_value = $(this).val();
        var res = rate_id.split("_");
        var net_weight = `#` + res[0] + `_net_weight`;
        var net_weight_value = $(net_weight).val();
        var amount = (rate_value * 2 * net_weight_value) / 100;

        $(`#` + res[0] + `_amount`).val(amount);
        global_amount = global_amount + amount;

        rmc_input_box.val(global_amount * 0.006);
        commission_input_box.val(global_amount * 0.05);

        var rmc_value = rmc_input_box.val();
        var comission_value = commission_input_box.val();
        var cooli_value = cooli_input_box.val();
            if (cooli_value.length <= 0) {
          cooli_value = 0;
        }

        var final_value =
          parseFloat(rmc_value) +
          parseFloat(comission_value) +
          parseFloat(cooli_value) +
          parseFloat(global_amount);
        total_amount.val(final_value);
    }



});